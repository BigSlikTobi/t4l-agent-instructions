from __future__ import annotations

import copy
from datetime import date, datetime
import hashlib
import json
import math
from pathlib import Path
import re
import unittest
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "contracts" / "coaching-contract.v1.schema.json"
FIXTURES = ROOT / "tests" / "fixtures" / "coaching_contract"


def _no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_no_duplicate_keys)


SCHEMA = load_json(SCHEMA_PATH)


def _jcs_float(number: float) -> str:
    if not math.isfinite(number):
        raise ValueError("RFC 8785 rejects non-finite numbers")
    if number == 0:
        return "0"
    negative = number < 0
    mantissa, marker, exponent_text = repr(abs(number)).lower().partition("e")
    exponent = int(exponent_text) if marker else 0
    whole, _, fraction = mantissa.partition(".")
    raw_digits = whole + fraction
    leading_zeroes = len(raw_digits) - len(raw_digits.lstrip("0"))
    digits = raw_digits[leading_zeroes:].rstrip("0")
    point = len(whole) + exponent - leading_zeroes
    scientific_exponent = point - 1
    if scientific_exponent < -6 or scientific_exponent >= 21:
        body = digits[0] + (("." + digits[1:]) if len(digits) > 1 else "")
        body += "e" + ("+" if scientific_exponent >= 0 else "") + str(scientific_exponent)
    elif point <= 0:
        body = "0." + ("0" * -point) + digits
    elif point >= len(digits):
        body = digits + ("0" * (point - len(digits)))
    else:
        body = digits[:point] + "." + digits[point:]
    return ("-" if negative else "") + body


def _utf16_key(value: str) -> bytes:
    try:
        return value.encode("utf-16-be")
    except UnicodeEncodeError as exc:
        raise ValueError("RFC 8785 rejects lone Unicode surrogates") from exc


def _canonical_text(value) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return _jcs_float(value)
    if isinstance(value, str):
        _utf16_key(value)
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return "[" + ",".join(_canonical_text(item) for item in value) + "]"
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise TypeError("RFC 8785 object keys must be strings")
        keys = sorted(value, key=_utf16_key)
        return "{" + ",".join(
            f"{_canonical_text(key)}:{_canonical_text(value[key])}" for key in keys
        ) + "}"
    raise TypeError(f"unsupported JSON value: {type(value).__name__}")


def canonical_json(value) -> bytes:
    """RFC 8785 JSON Canonicalization Scheme bytes for JSON-compatible values."""
    return _canonical_text(value).encode("utf-8")


def payload_digest(payload) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(payload)).hexdigest()


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("date-time must include an offset")
    return parsed


def revision_counter(value: str) -> int:
    return int(value.split("_", 2)[1])


def resolve_json_pointer(document, pointer: str):
    """Resolve a non-empty RFC 6901 pointer or raise ValueError."""
    if not pointer.startswith("/"):
        raise ValueError("JSON Pointer must start with /")
    value = document
    for raw_token in pointer[1:].split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if isinstance(value, dict) and token in value:
            value = value[token]
        elif isinstance(value, list) and token.isdigit() and int(token) < len(value):
            value = value[int(token)]
        else:
            raise ValueError(f"JSON Pointer does not resolve: {pointer}")
    return value


class SmallDraft202012Validator:
    """Dependency-free validator for the JSON Schema keywords used by this contract."""

    def __init__(self, root_schema):
        self.root = root_schema

    def validate(self, instance) -> list[str]:
        return self._errors(instance, self.root, "$")

    def _resolve(self, ref: str):
        if not ref.startswith("#/"):
            raise AssertionError(f"test validator only supports local refs: {ref}")
        node = self.root
        for token in ref[2:].split("/"):
            node = node[token.replace("~1", "/").replace("~0", "~")]
        return node

    def _errors(self, instance, schema, path: str) -> list[str]:
        if "$ref" in schema:
            return self._errors(instance, self._resolve(schema["$ref"]), path)

        errors = []
        if "oneOf" in schema:
            branch_errors = [self._errors(instance, item, path) for item in schema["oneOf"]]
            valid = sum(not item for item in branch_errors)
            if valid != 1:
                detail = next((item[0] for item in branch_errors if item), "multiple branches matched")
                errors.append(f"{path}: oneOf matched {valid} branches ({detail})")
                return errors
        if "anyOf" in schema:
            branch_errors = [self._errors(instance, item, path) for item in schema["anyOf"]]
            if all(branch_errors):
                errors.append(f"{path}: no anyOf branch matched")
                return errors
        for part in schema.get("allOf", []):
            errors.extend(self._errors(instance, part, path))
        if "if" in schema:
            condition_matches = not self._errors(instance, schema["if"], path)
            selected = schema.get("then" if condition_matches else "else")
            if selected is not None:
                errors.extend(self._errors(instance, selected, path))

        expected_type = schema.get("type")
        if expected_type is not None and not self._is_type(instance, expected_type):
            return errors + [f"{path}: expected {expected_type}, got {type(instance).__name__}"]

        if "const" in schema and not self._same_json(instance, schema["const"]):
            errors.append(f"{path}: expected const {schema['const']!r}")
        if "enum" in schema and not any(self._same_json(instance, value) for value in schema["enum"]):
            errors.append(f"{path}: value {instance!r} is not in enum")

        if isinstance(instance, dict):
            for name in schema.get("required", []):
                if name not in instance:
                    errors.append(f"{path}: missing required property {name!r}")
            properties = schema.get("properties", {})
            for name, child in instance.items():
                if name in properties:
                    errors.extend(self._errors(child, properties[name], f"{path}.{name}"))
                elif schema.get("additionalProperties") is False:
                    errors.append(f"{path}: unexpected property {name!r}")
            if len(instance) < schema.get("minProperties", 0):
                errors.append(f"{path}: too few properties")

        if isinstance(instance, list):
            if len(instance) < schema.get("minItems", 0):
                errors.append(f"{path}: too few items")
            if schema.get("uniqueItems"):
                encoded = [canonical_json(item) for item in instance]
                if len(set(encoded)) != len(encoded):
                    errors.append(f"{path}: items are not unique")
            if "items" in schema:
                for index, item in enumerate(instance):
                    errors.extend(self._errors(item, schema["items"], f"{path}[{index}]"))

        if isinstance(instance, str):
            if len(instance) < schema.get("minLength", 0):
                errors.append(f"{path}: string is too short")
            if "maxLength" in schema and len(instance) > schema["maxLength"]:
                errors.append(f"{path}: string is too long")
            if "pattern" in schema and re.search(schema["pattern"], instance) is None:
                errors.append(f"{path}: string does not match {schema['pattern']!r}")
            errors.extend(self._format_errors(instance, schema.get("format"), path))

        if isinstance(instance, int) and not isinstance(instance, bool):
            if "minimum" in schema and instance < schema["minimum"]:
                errors.append(f"{path}: number is below minimum")
            if "maximum" in schema and instance > schema["maximum"]:
                errors.append(f"{path}: number is above maximum")
        return errors

    @staticmethod
    def _same_json(left, right) -> bool:
        return type(left) is type(right) and left == right

    @staticmethod
    def _is_type(value, expected) -> bool:
        if isinstance(expected, list):
            return any(SmallDraft202012Validator._is_type(value, item) for item in expected)
        checks = {
            "object": lambda: isinstance(value, dict),
            "array": lambda: isinstance(value, list),
            "string": lambda: isinstance(value, str),
            "integer": lambda: isinstance(value, int) and not isinstance(value, bool),
            "number": lambda: isinstance(value, (int, float)) and not isinstance(value, bool),
            "boolean": lambda: isinstance(value, bool),
            "null": lambda: value is None,
        }
        return checks[expected]()

    @staticmethod
    def _format_errors(value: str, format_name: str | None, path: str) -> list[str]:
        try:
            if format_name == "date-time":
                parse_time(value)
            elif format_name == "date":
                if len(value) != 10 or date.fromisoformat(value).isoformat() != value:
                    raise ValueError("not canonical ISO date")
            elif format_name == "iana-time-zone":
                ZoneInfo(value)
        except (ValueError, ZoneInfoNotFoundError):
            return [f"{path}: invalid {format_name}"]
        return []


SHAPE_VALIDATOR = SmallDraft202012Validator(SCHEMA)


def _source_errors(source: dict, generated_at: datetime, path: str) -> list[str]:
    received = parse_time(source["receivedAt"])
    evaluated = parse_time(source["freshness"]["evaluatedAt"])
    errors = []
    if source["availability"] == "available":
        source_time = parse_time(source["sourceTime"])
        if not source_time <= received <= evaluated <= generated_at:
            errors.append(f"{path}: source/received/evaluated/generated time order is invalid")
        age = (evaluated - source_time).total_seconds()
        expected = "fresh" if age <= source["freshness"]["maxAgeSeconds"] else "stale"
        if source["freshness"]["status"] != expected:
            errors.append(f"{path}: freshness status does not match source age")
    elif not received <= evaluated <= generated_at:
        errors.append(f"{path}: missing-source received/evaluated/generated order is invalid")
    return errors


def accepted_freshness(document: dict) -> list[str]:
    generated = parse_time(document["generatedAt"])
    errors = []
    for index, source in enumerate(document["sources"]):
        errors.extend(_source_errors(source, generated, f"sources[{index}]"))
    return errors


def accepted_session_identity(document: dict) -> list[str]:
    active_id = document["activeSessionId"]
    active = document["activeSession"]
    if (active_id is None) != (active is None):
        return ["activeSessionId and activeSession nullability differ"]
    if active is not None and active["sessionId"] != active_id:
        return ["activeSessionId does not match activeSession.sessionId"]
    return []


def accepted_provenance_coverage(document: dict) -> list[str]:
    errors = []
    context_root = {"acceptedState": document}
    for index, source in enumerate(document["sources"]):
        if source["path"] != "/acceptedState":
            errors.append(f"sources[{index}].path does not name the authoritative acceptedState")
            continue
        try:
            record = resolve_json_pointer(context_root, source["path"])
            for pointer in source["fields"]:
                resolve_json_pointer(record, pointer)
        except ValueError as exc:
            errors.append(f"sources[{index}]: {exc}")
    for field, value in document["state"].items():
        escaped = field.replace("~", "~0").replace("/", "~1")
        pointer = f"/state/{escaped}"
        covering = [source for source in document["sources"] if pointer in source["fields"]]
        if not covering:
            errors.append(f"{pointer} has no provenance source")
        elif value is not None and not any(source["availability"] == "available" for source in covering):
            errors.append(f"{pointer} is non-null but has no available source")
    return errors


def _standing_consent_errors(consent: dict, at: datetime, path: str) -> list[str]:
    granted = parse_time(consent["grantedAt"])
    valid_from = parse_time(consent["validFrom"])
    valid_until = parse_time(consent["validUntil"]) if consent["validUntil"] is not None else None
    revoked = parse_time(consent["revokedAt"]) if consent["revokedAt"] is not None else None
    status = consent["status"]
    errors = []
    if granted > valid_from:
        errors.append(f"{path}: grantedAt is after validFrom")
    if valid_until is not None and valid_from >= valid_until:
        errors.append(f"{path}: validUntil is not after validFrom")
    if status == "active":
        if revoked is not None:
            errors.append(f"{path}: active consent has revokedAt")
        if at < valid_from or (valid_until is not None and at >= valid_until):
            errors.append(f"{path}: active consent is outside its validity window")
    elif status == "expired":
        if valid_until is None or at < valid_until:
            errors.append(f"{path}: expired status does not match validUntil")
        if revoked is not None:
            errors.append(f"{path}: expired consent also has revokedAt")
    elif status == "revoked":
        if revoked is None or revoked < granted or revoked > at:
            errors.append(f"{path}: revoked status does not match revokedAt")
    return errors


def accepted_consent_state(document: dict) -> list[str]:
    generated = parse_time(document["generatedAt"])
    errors = []
    consent_ids = [consent["consentId"] for consent in document["state"]["standingConsents"]]
    if len(consent_ids) != len(set(consent_ids)):
        errors.append("standingConsents contains duplicate consentId values")
    for index, consent in enumerate(document["state"]["standingConsents"]):
        errors.extend(_standing_consent_errors(consent, generated, f"standingConsents[{index}]"))
    return errors


def proposal_time_and_freshness(document: dict) -> list[str]:
    base = document["baseFreshness"]
    source = parse_time(base["sourceTime"])
    evaluated = parse_time(base["evaluatedAt"])
    generated = parse_time(document["generatedAt"])
    expires = parse_time(document["expiresAt"])
    errors = []
    if not source <= evaluated <= generated < expires:
        errors.append("proposal source/evaluated/generated/expiry order is invalid")
    if (evaluated - source).total_seconds() > base["maxAgeSeconds"]:
        errors.append("proposal base context is stale")
    if (generated - source).total_seconds() > base["maxAgeSeconds"]:
        errors.append("proposal base context was stale by generation time")
    if document["payloadDigest"] != payload_digest(document["payload"]):
        errors.append("proposal payloadDigest does not match RFC 8785 payload bytes")
    return errors


def proposal_input_sources(document: dict) -> list[str]:
    sources = document["inputSources"]
    generated = parse_time(document["generatedAt"])
    errors = []
    for index, source in enumerate(sources):
        errors.extend(_source_errors(source, generated, f"inputSources[{index}]"))
        if source["availability"] != "available" or source["freshness"]["status"] != "fresh":
            errors.append(f"inputSources[{index}] is not available and fresh")
    base = document["baseFreshness"]
    if parse_time(base["sourceTime"]) != min(parse_time(source["sourceTime"]) for source in sources):
        errors.append("baseFreshness.sourceTime is not the oldest input source")
    if parse_time(base["evaluatedAt"]) != max(
        parse_time(source["freshness"]["evaluatedAt"]) for source in sources
    ):
        errors.append("baseFreshness.evaluatedAt is not the latest input evaluation")
    if base["maxAgeSeconds"] != min(source["freshness"]["maxAgeSeconds"] for source in sources):
        errors.append("baseFreshness.maxAgeSeconds is not the strictest input window")
    return errors


def receipt_time_order(document: dict) -> list[str]:
    evaluated = parse_time(document["evaluatedAt"])
    source = parse_time(document["sourceTime"])
    generated = parse_time(document["generatedAt"])
    errors = []
    if document["outcome"] == "applied":
        applied = parse_time(document["appliedAt"])
        if not evaluated <= applied <= source <= generated:
            errors.append("receipt evaluated/applied/source/generated order is invalid")
        if revision_counter(document["appliedRevision"]) <= revision_counter(
            document["baseRevision"]
        ):
            errors.append("appliedRevision must advance beyond baseRevision")
        proof = document.get("explicitReviewProof")
        if proof is not None:
            proposal = proof["proposal"]
            errors.extend(validate_semantics(proposal))
            for field in (
                "requestId",
                "resultId",
                "payloadDigest",
                "changeClass",
                "applyMode",
                "baseRevision",
                "target",
            ):
                if document[field] != proposal[field]:
                    errors.append(f"explicit proof proposal {field} does not match receipt")
            reviewed = parse_time(proof["reviewedAt"])
            if not parse_time(proposal["generatedAt"]) <= reviewed <= evaluated:
                errors.append("explicit review/proposal/evaluation time order is invalid")
            if evaluated >= parse_time(proposal["expiresAt"]):
                errors.append("explicit-review proposal was expired at evaluation")
    elif not evaluated <= source <= generated:
        errors.append("receipt evaluated/source/generated order is invalid")
    return errors


def automatic_receipt_proof(document: dict) -> list[str]:
    if document.get("outcome") != "applied" or document.get("applyMode") != "automatic":
        return []
    proof = document["automaticApplyProof"]
    proposal = proof["proposal"]
    accepted = proof["acceptedStateAtEvaluation"]
    consent = proof["standingConsent"]
    errors = validate_semantics(proposal)
    for field in (
        "requestId",
        "resultId",
        "payloadDigest",
        "changeClass",
        "applyMode",
        "baseRevision",
        "target",
    ):
        if document[field] != proposal[field]:
            errors.append(f"automatic proof proposal {field} does not match receipt")
    if proposal["payloadDigest"] != payload_digest(proposal["payload"]):
        errors.append("automatic proof payloadDigest does not match proposal payload")
    if accepted["contextRevision"] != document["baseRevision"]:
        errors.append("automatic proof accepted revision does not match baseRevision")
    if accepted["target"] != document["target"]:
        errors.append("automatic proof accepted target does not match proposal target")
    evaluated = parse_time(document["evaluatedAt"])
    if parse_time(accepted["sourceTime"]) > evaluated:
        errors.append("accepted-state snapshot sourceTime is after receipt evaluation")
    if not parse_time(proposal["generatedAt"]) <= evaluated < parse_time(proposal["expiresAt"]):
        errors.append("automatic proposal was not unexpired at evaluation")
    errors.extend(_standing_consent_errors(consent, evaluated, "automatic standingConsent"))
    if consent["status"] != "active":
        errors.append("standing consent status is not active")
    if consent["revokedAt"] is not None:
        errors.append("standing consent was revoked")
    if consent["consentId"] != proposal["review"]["standingConsentId"]:
        errors.append("standing consent ID does not match proposal")
    if document["changeClass"] not in consent["scopes"]:
        errors.append("standing consent does not cover change class")
    if parse_time(consent["validFrom"]) > evaluated:
        errors.append("standing consent was not yet valid")
    if consent["validUntil"] is not None and evaluated >= parse_time(consent["validUntil"]):
        errors.append("standing consent was expired")
    if accepted["activeSessionId"] is not None:
        errors.append("automatic application conflicts with an active session")
    return errors


def current_request_time(document: dict) -> list[str]:
    errors = []
    generated = parse_time(document["generatedAt"])
    for index, request in enumerate(document["currentRequests"]):
        source = parse_time(request["sourceTime"])
        created = parse_time(request["createdAt"])
        if not source <= created <= generated:
            errors.append(f"currentRequests[{index}] source/created/context time order is invalid")
        if request["expiresAt"] is not None and generated >= parse_time(request["expiresAt"]):
            errors.append(f"currentRequests[{index}] is already expired")
        for source_index, provenance in enumerate(request["sources"]):
            expected_path = f"/currentRequests/{index}"
            if provenance["path"] != expected_path:
                errors.append(
                    f"currentRequests[{index}].sources[{source_index}].path is not {expected_path}"
                )
            else:
                try:
                    record = resolve_json_pointer(document, provenance["path"])
                    for pointer in provenance["fields"]:
                        resolve_json_pointer(record, pointer)
                except ValueError as exc:
                    errors.append(f"currentRequests[{index}].sources[{source_index}]: {exc}")
            errors.extend(
                _source_errors(provenance, generated, f"currentRequests[{index}].sources[{source_index}]")
            )
    return errors


def request_history_time(document: dict) -> list[str]:
    generated = parse_time(document["generatedAt"])
    errors = []
    current_ids = [request["requestId"] for request in document["currentRequests"]]
    history_ids = [request["requestId"] for request in document["requestHistory"]]
    if len(current_ids) != len(set(current_ids)):
        errors.append("currentRequests contains duplicate requestId values")
    if len(history_ids) != len(set(history_ids)):
        errors.append("requestHistory contains duplicate requestId values")
    if set(current_ids) & set(history_ids):
        errors.append("a requestId appears in both currentRequests and requestHistory")
    receipts = {receipt["receiptId"]: receipt for receipt in document["appliedReceipts"]}
    for index, request in enumerate(document["requestHistory"]):
        source = parse_time(request["sourceTime"])
        created = parse_time(request["createdAt"])
        closed = parse_time(request["closedAt"])
        if not source <= created <= closed <= generated:
            errors.append(f"requestHistory[{index}] source/created/closed/context time order is invalid")
        expires = parse_time(request["expiresAt"]) if request["expiresAt"] is not None else None
        if expires is not None and created >= expires:
            errors.append(f"requestHistory[{index}] expiry is not after creation")
        if request["status"] == "expired" and (expires is None or expires > closed):
            errors.append(f"requestHistory[{index}] expired status does not match expiry")
        if request["status"] in {"consumed", "rejected"}:
            receipt = receipts.get(request["receiptId"])
            if receipt is None:
                errors.append(f"requestHistory[{index}] does not link an existing receipt")
            else:
                if receipt["requestId"] != request["requestId"]:
                    errors.append(f"requestHistory[{index}] requestId does not match its receipt")
                expected_applied = request["status"] == "consumed"
                if (receipt["outcome"] == "applied") != expected_applied:
                    errors.append(f"requestHistory[{index}] status does not match receipt outcome")
        for source_index, provenance in enumerate(request["sources"]):
            expected_path = f"/requestHistory/{index}"
            if provenance["path"] != expected_path:
                errors.append(
                    f"requestHistory[{index}].sources[{source_index}].path is not {expected_path}"
                )
            else:
                try:
                    record = resolve_json_pointer(document, provenance["path"])
                    for pointer in provenance["fields"]:
                        resolve_json_pointer(record, pointer)
                except ValueError as exc:
                    errors.append(f"requestHistory[{index}].sources[{source_index}]: {exc}")
            errors.extend(
                _source_errors(provenance, generated, f"requestHistory[{index}].sources[{source_index}]")
            )
    return errors


def _receipt_embedded_proposal(receipt: dict):
    if receipt["outcome"] != "applied":
        return None
    if receipt["applyMode"] == "automatic":
        return receipt["automaticApplyProof"]["proposal"]
    return receipt["explicitReviewProof"]["proposal"]


def planning_context_integrity(document: dict) -> list[str]:
    generated = parse_time(document["generatedAt"])
    accepted = document["acceptedState"]
    errors = []
    if parse_time(accepted["generatedAt"]) > generated:
        errors.append("acceptedState was generated after its planningContext")

    receipt_ids = [receipt["receiptId"] for receipt in document["appliedReceipts"]]
    if len(receipt_ids) != len(set(receipt_ids)):
        errors.append("appliedReceipts contains duplicate receiptId values")

    current_requests = document["currentRequests"]
    authoritative_sources = list(accepted["sources"])
    for request in current_requests:
        authoritative_sources.extend(request["sources"])
    source_ids = [
        source["sourceId"] for source in authoritative_sources if source["sourceId"] is not None
    ]
    if len(source_ids) != len(set(source_ids)):
        errors.append("authoritative current provenance contains duplicate sourceId values")

    for proposal in document["proposals"]:
        if parse_time(proposal["generatedAt"]) > generated:
            errors.append(f"proposal {proposal['resultId']} was generated after its planningContext")
        if proposal["baseRevision"] != accepted["contextRevision"]:
            errors.append(f"proposal {proposal['resultId']} baseRevision is not current")
        requests = [
            request for request in current_requests if request["requestId"] == proposal["requestId"]
        ]
        if len(requests) != 1:
            errors.append(f"proposal {proposal['resultId']} has no unique current request")
        else:
            request = requests[0]
            if request["target"] != proposal["target"]:
                errors.append(f"proposal {proposal['resultId']} target does not match its request")
            if parse_time(proposal["generatedAt"]) < parse_time(request["createdAt"]):
                errors.append(f"proposal {proposal['resultId']} predates its request")
        for index, source in enumerate(proposal["inputSources"]):
            try:
                record = resolve_json_pointer(document, source["path"])
                for pointer in source["fields"]:
                    resolve_json_pointer(record, pointer)
            except ValueError as exc:
                errors.append(f"proposal {proposal['resultId']} inputSources[{index}]: {exc}")
            candidates = []
            for candidate in authoritative_sources:
                same_snapshot = all(
                    source[key] == candidate[key]
                    for key in (
                        "sourceId",
                        "kind",
                        "path",
                        "sourceRevision",
                        "artifactId",
                        "sourceTime",
                        "receivedAt",
                        "availability",
                        "freshness",
                    )
                )
                if same_snapshot and set(source["fields"]).issubset(candidate["fields"]):
                    candidates.append(candidate)
            if len(candidates) != 1:
                errors.append(
                    f"proposal {proposal['resultId']} inputSources[{index}] is not authoritative"
                )

    embedded = [
        proposal
        for receipt in document["appliedReceipts"]
        if (proposal := _receipt_embedded_proposal(receipt)) is not None
    ]
    errors.extend(proposal_idempotency_errors(document["proposals"] + embedded))
    active_ids = {proposal["resultId"] for proposal in document["proposals"]}
    terminal_ids = {receipt["resultId"] for receipt in document["appliedReceipts"]}
    for result_id in sorted(active_ids & terminal_ids):
        errors.append(f"terminal result {result_id} is still present as a current proposal")

    accepted_counter = revision_counter(accepted["contextRevision"])
    for receipt in document["appliedReceipts"]:
        if parse_time(receipt["generatedAt"]) > generated:
            errors.append(f"receipt {receipt['receiptId']} was generated after its planningContext")
        receipt_proposal = _receipt_embedded_proposal(receipt)
        if receipt_proposal is not None:
            for field in (
                "requestId",
                "resultId",
                "payloadDigest",
                "changeClass",
                "applyMode",
                "baseRevision",
                "target",
            ):
                if receipt[field] != receipt_proposal[field]:
                    errors.append(f"receipt/embedded proposal {field} mismatch")
        if receipt["outcome"] == "applied":
            applied = receipt["appliedRevision"]
            applied_counter = revision_counter(applied)
            if accepted_counter < applied_counter:
                errors.append(
                    f"acceptedState predates applied revision {applied} from {receipt['receiptId']}"
                )
            elif accepted_counter == applied_counter and accepted["contextRevision"] != applied:
                errors.append("equal revision counters carry conflicting revision tokens")

    history_by_receipt = {
        request["receiptId"]: request
        for request in document["requestHistory"]
        if request["receiptId"] is not None
    }
    for receipt in document["appliedReceipts"]:
        if receipt["receiptId"] not in history_by_receipt:
            errors.append(f"receipt {receipt['receiptId']} has no terminal request-history record")
    return errors


INVARIANT_EVALUATORS = {
    "accepted-freshness-v1": accepted_freshness,
    "accepted-session-identity-v1": accepted_session_identity,
    "accepted-provenance-coverage-v1": accepted_provenance_coverage,
    "accepted-consent-state-v1": accepted_consent_state,
    "proposal-time-and-freshness-v1": proposal_time_and_freshness,
    "proposal-input-sources-v1": proposal_input_sources,
    "receipt-time-order-v1": receipt_time_order,
    "automatic-receipt-proof-v1": automatic_receipt_proof,
    "current-request-time-v1": current_request_time,
    "request-history-time-v1": request_history_time,
    "planning-context-integrity-v1": planning_context_integrity,
}


def validate_semantics(document: dict) -> list[str]:
    errors = []
    message_type = document.get("messageType")
    for invariant in SCHEMA["x-t4l-invariants"]:
        if invariant["messageType"] != message_type or invariant.get("scope") == "corpus":
            continue
        when = invariant.get("when", {})
        if any(document.get(key) != value for key, value in when.items()):
            continue
        errors.extend(INVARIANT_EVALUATORS[invariant["id"]](document))
    if message_type == "planning_context":
        errors.extend(validate_semantics(document["acceptedState"]))
        for proposal in document["proposals"]:
            errors.extend(validate_semantics(proposal))
        for receipt in document["appliedReceipts"]:
            errors.extend(validate_semantics(receipt))
    return errors


def validate_contract(document: dict) -> list[str]:
    shape_errors = SHAPE_VALIDATOR.validate(document)
    return shape_errors or validate_semantics(document)


def proposal_idempotency_errors(proposals: list[dict]) -> list[str]:
    seen = {}
    errors = []
    for proposal in proposals:
        result_id = proposal["resultId"]
        canonical = canonical_json(proposal)
        previous = seen.setdefault(result_id, canonical)
        if previous != canonical:
            errors.append(f"{result_id} maps to different canonical proposal envelopes")
    return errors


class CoachingContractTests(unittest.TestCase):
    @staticmethod
    def _planning_context_with_application(proposal: dict, receipt: dict, generated_at: str) -> dict:
        context = load_json(FIXTURES / "must_accept" / "planning_context_separates_records.json")
        context["generatedAt"] = generated_at
        request = context["currentRequests"].pop(0)
        request.update(
            {
                "requestId": proposal["requestId"],
                "status": "consumed",
                "target": copy.deepcopy(proposal["target"]),
                "closedAt": receipt["generatedAt"],
                "receiptId": receipt["receiptId"],
                "reasonCode": None,
            }
        )
        history_index = len(context["requestHistory"])
        for source in request["sources"]:
            source["path"] = f"/requestHistory/{history_index}"
        context["requestHistory"].append(request)
        context["proposals"] = []
        context["appliedReceipts"] = [receipt]
        if receipt["outcome"] == "applied":
            accepted = context["acceptedState"]
            accepted["contextRevision"] = receipt["appliedRevision"]
            accepted["generatedAt"] = receipt["generatedAt"]
            primary_source = accepted["sources"][0]
            primary_source["sourceRevision"] = receipt["appliedRevision"]
            primary_source["sourceTime"] = receipt["sourceTime"]
            primary_source["receivedAt"] = receipt["sourceTime"]
            primary_source["freshness"]["evaluatedAt"] = receipt["generatedAt"]
            if proposal["changeClass"] == "full_block":
                accepted["state"]["activeBlock"] = copy.deepcopy(proposal["payload"]["block"])
        return context

    @staticmethod
    def _planning_context_with_current_proposal(proposal: dict, generated_at: str) -> dict:
        context = load_json(FIXTURES / "must_accept" / "planning_context_separates_records.json")
        context["generatedAt"] = generated_at
        request = context["currentRequests"][0]
        request["requestId"] = proposal["requestId"]
        request["target"] = copy.deepcopy(proposal["target"])
        authoritative = context["acceptedState"]["sources"][0]
        proposed_source = proposal["inputSources"][0]
        for key in (
            "sourceId",
            "kind",
            "path",
            "sourceRevision",
            "artifactId",
            "sourceTime",
            "receivedAt",
            "availability",
            "freshness",
        ):
            authoritative[key] = copy.deepcopy(proposed_source[key])
        authoritative["fields"] = sorted(
            set(authoritative["fields"]) | set(proposed_source["fields"])
        )
        context["proposals"] = [copy.deepcopy(proposal)]
        context["appliedReceipts"] = []
        return context

    def test_schema_is_strict_draft_2020_12_and_has_no_duplicate_keys(self):
        self.assertEqual(SCHEMA["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(SCHEMA["$id"], "urn:t4l:coaching-contract:1.0.0")
        self.assertEqual(len(SCHEMA["oneOf"]), 4)

    def test_canonical_json_uses_rfc8785_number_and_key_rules(self):
        cases = [
            (-0.0, "0"),
            (82.0, "82"),
            (1e-6, "0.000001"),
            (1e-7, "1e-7"),
            (1e20, "100000000000000000000"),
            (1e21, "1e+21"),
        ]
        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(canonical_json(value), expected.encode("ascii"))
        self.assertEqual(
            canonical_json({"\ue000": "bmp", "\U00010000": "astral"}),
            '{"\U00010000":"astral","\ue000":"bmp"}'.encode("utf-8"),
        )
        with self.assertRaises(ValueError):
            canonical_json(float("nan"))

    def test_must_accept_golden_corpus(self):
        for path in sorted((FIXTURES / "must_accept").glob("*.json")):
            with self.subTest(path=path.name):
                self.assertEqual(validate_contract(load_json(path)), [])

    def test_must_reject_golden_corpus(self):
        for path in sorted((FIXTURES / "must_reject").glob("*.json")):
            with self.subTest(path=path.name):
                self.assertTrue(validate_contract(load_json(path)), path.name)

    def test_automatic_receipt_safety_mutations_are_rejected(self):
        path = FIXTURES / "must_accept" / "applied_receipt_automatic_minor.json"
        valid = load_json(path)
        mutations = {
            "target": lambda item: item["automaticApplyProof"]["proposal"]["target"].update(
                {"localDate": "2026-08-02"}
            ),
            "base revision": lambda item: item["automaticApplyProof"]["acceptedStateAtEvaluation"].update(
                {"contextRevision": "ctx_40_cccccccc"}
            ),
            "expiry": lambda item: item["automaticApplyProof"]["proposal"].update(
                {"expiresAt": "2026-08-01T08:04:59Z"}
            ),
            "consent validity": lambda item: item["automaticApplyProof"]["standingConsent"].update(
                {"validUntil": "2026-08-01T08:05:00Z"}
            ),
            "consent scope": lambda item: item["automaticApplyProof"]["standingConsent"].update(
                {"scopes": ["guidance"]}
            ),
            "consent status": lambda item: item["automaticApplyProof"]["standingConsent"].update(
                {"status": "expired", "validUntil": "2026-08-01T08:04:59Z"}
            ),
            "consent revoked": lambda item: item["automaticApplyProof"]["standingConsent"].update(
                {"status": "revoked", "revokedAt": "2026-08-01T08:04:00Z"}
            ),
            "consent identity": lambda item: item["automaticApplyProof"]["standingConsent"].update(
                {"consentId": "cns_ffffffffffffffff"}
            ),
            "consent grant order": lambda item: item["automaticApplyProof"]["standingConsent"].update(
                {"grantedAt": "2026-08-01T08:06:00Z"}
            ),
            "active session": lambda item: item["automaticApplyProof"]["acceptedStateAtEvaluation"].update(
                {"activeSessionId": "ses_eeeeeeeeeeeeeeee"}
            ),
            "accepted source time": lambda item: item["automaticApplyProof"][
                "acceptedStateAtEvaluation"
            ].update({"sourceTime": "2026-08-01T08:05:01Z"}),
            "accepted target": lambda item: item["automaticApplyProof"][
                "acceptedStateAtEvaluation"
            ]["target"].update({"localDate": "2026-08-02"}),
            "proposal base revision": lambda item: item["automaticApplyProof"]["proposal"].update(
                {"baseRevision": "ctx_40_cccccccc"}
            ),
            "proposal apply mode": lambda item: item["automaticApplyProof"]["proposal"].update(
                {
                    "applyMode": "explicit_review",
                    "review": {
                        "mode": "explicit_review",
                        "required": True,
                        "standingConsentId": None,
                    },
                }
            ),
            "digest": lambda item: item["automaticApplyProof"]["proposal"].update(
                {"payloadDigest": "sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"}
            ),
        }
        for name, mutate in mutations.items():
            with self.subTest(condition=name):
                candidate = copy.deepcopy(valid)
                mutate(candidate)
                self.assertTrue(automatic_receipt_proof(candidate), name)
                self.assertTrue(validate_contract(candidate))

    def test_provenance_uses_json_pointers_and_immutable_revisions(self):
        valid = load_json(FIXTURES / "must_accept" / "accepted_state_fresh.json")
        invalid_pointer = copy.deepcopy(valid)
        invalid_pointer["sources"][0]["fields"][0] = "state.activeBlock"
        self.assertTrue(validate_contract(invalid_pointer))

        missing_revision = copy.deepcopy(valid)
        missing_revision["sources"][0]["sourceRevision"] = None
        self.assertIsNotNone(missing_revision["sources"][0]["artifactId"])
        self.assertTrue(validate_contract(missing_revision))

        unresolved_path = copy.deepcopy(valid)
        unresolved_path["sources"][0]["path"] = "/not/the/accepted/state"
        self.assertTrue(accepted_provenance_coverage(unresolved_path))
        self.assertTrue(validate_contract(unresolved_path))

    def test_accepted_state_rejects_duplicate_consent_ids(self):
        valid = load_json(FIXTURES / "must_accept" / "accepted_state_fresh.json")
        duplicate = copy.deepcopy(valid["state"]["standingConsents"][0])
        duplicate["scopes"] = ["guidance"]
        valid["state"]["standingConsents"].append(duplicate)
        self.assertTrue(accepted_consent_state(valid))
        self.assertTrue(validate_contract(valid))

    def test_request_lifecycle_separates_current_and_history(self):
        valid = load_json(FIXTURES / "must_accept" / "planning_context_separates_records.json")
        self.assertEqual(validate_contract(valid), [])
        self.assertEqual(valid["requestHistory"][0]["status"], "expired")

        terminal_in_current = copy.deepcopy(valid)
        terminal_in_current["currentRequests"][0]["status"] = "expired"
        self.assertTrue(validate_contract(terminal_in_current))

        already_expired = copy.deepcopy(valid)
        already_expired["currentRequests"][0]["expiresAt"] = "2026-08-01T08:00:59Z"
        self.assertTrue(validate_contract(already_expired))

        duplicate_across_lifecycle = copy.deepcopy(valid)
        duplicate_across_lifecycle["requestHistory"][0]["requestId"] = valid["currentRequests"][0][
            "requestId"
        ]
        self.assertTrue(validate_contract(duplicate_across_lifecycle))

        uncorrelated_consumed = copy.deepcopy(valid)
        uncorrelated_consumed["requestHistory"][0].update(
            {"status": "consumed", "receiptId": None, "reasonCode": None}
        )
        self.assertTrue(validate_contract(uncorrelated_consumed))

    def test_planning_context_rejects_receipt_proposal_identity_mismatch(self):
        proposal = load_json(FIXTURES / "must_accept" / "proposal_full_block_explicit.json")
        receipt = load_json(FIXTURES / "must_accept" / "applied_receipt_explicit_full_block.json")
        context = self._planning_context_with_application(
            proposal, receipt, "2026-08-01T08:12:00Z"
        )
        self.assertEqual(validate_contract(context), [])

        mismatch = copy.deepcopy(context)
        mismatch["appliedReceipts"][0]["target"]["localDate"] = "2026-08-05"
        self.assertTrue(planning_context_integrity(mismatch))
        self.assertTrue(validate_contract(mismatch))

        stale_state = copy.deepcopy(context)
        stale_state["acceptedState"]["contextRevision"] = proposal["baseRevision"]
        stale_state["acceptedState"]["sources"][0]["sourceRevision"] = proposal[
            "baseRevision"
        ]
        errors = planning_context_integrity(stale_state)
        self.assertTrue(any("predates applied revision" in error for error in errors), errors)
        self.assertTrue(validate_contract(stale_state))

        duplicate_receipt = copy.deepcopy(context)
        duplicate_receipt["appliedReceipts"].append(
            copy.deepcopy(duplicate_receipt["appliedReceipts"][0])
        )
        errors = planning_context_integrity(duplicate_receipt)
        self.assertTrue(any("duplicate receiptId" in error for error in errors), errors)
        self.assertTrue(validate_contract(duplicate_receipt))

    def test_planning_context_links_requests_and_input_provenance(self):
        proposal = load_json(FIXTURES / "must_accept" / "proposal_full_block_explicit.json")
        valid = self._planning_context_with_current_proposal(
            proposal, "2026-08-01T08:03:00Z"
        )
        self.assertEqual(validate_contract(valid), [])

        mutations = {
            "requestId": lambda item: item["proposals"][0].update(
                {"requestId": "req_9999999999999999"}
            ),
            "sourceId": lambda item: item["proposals"][0]["inputSources"][0].update(
                {"sourceId": "src_invented1"}
            ),
            "sourceRevision": lambda item: item["proposals"][0]["inputSources"][0].update(
                {"sourceRevision": "srcv_invented1"}
            ),
            "path": lambda item: item["proposals"][0]["inputSources"][0].update(
                {"path": "/not/the/accepted/state"}
            ),
            "field": lambda item: item["proposals"][0]["inputSources"][0].update(
                {"fields": ["/state/notReal"]}
            ),
            "freshness window": lambda item: item["proposals"][0]["inputSources"][0][
                "freshness"
            ].update({"maxAgeSeconds": 86400}),
        }
        for name, mutate in mutations.items():
            with self.subTest(link=name):
                candidate = copy.deepcopy(valid)
                mutate(candidate)
                self.assertTrue(planning_context_integrity(candidate), name)
                self.assertTrue(validate_contract(candidate))

    def test_terminal_receipt_keeps_full_proposal_out_of_current_set(self):
        receipt = load_json(FIXTURES / "must_accept" / "applied_receipt_automatic_minor.json")
        proposal = copy.deepcopy(receipt["automaticApplyProof"]["proposal"])
        proposal["baseFreshness"].update(
            {"sourceTime": "2026-08-01T07:55:00Z", "evaluatedAt": "2026-08-01T08:00:00Z"}
        )
        proposal["inputSources"][0].update(
            {
                "sourceId": "src_daystate1",
                "path": "/acceptedState",
                "fields": ["/state/activeBlock"],
                "sourceRevision": "ctx_41_aaaaaaaa",
                "artifactId": "art_phone_state:latest",
                "sourceTime": "2026-08-01T07:55:00Z",
                "receivedAt": "2026-08-01T07:55:02Z",
            }
        )
        proposal["inputSources"][0]["freshness"]["evaluatedAt"] = "2026-08-01T08:00:00Z"
        receipt["automaticApplyProof"]["proposal"] = copy.deepcopy(proposal)
        context = self._planning_context_with_application(
            proposal, receipt, "2026-08-01T08:06:00Z"
        )
        context["acceptedState"]["state"]["standingConsents"] = [
            copy.deepcopy(receipt["automaticApplyProof"]["standingConsent"])
        ]
        self.assertEqual(validate_contract(context), [])
        self.assertEqual(context["proposals"], [])

        terminal_left_active = copy.deepcopy(context)
        terminal_left_active["proposals"] = [copy.deepcopy(proposal)]
        errors = planning_context_integrity(terminal_left_active)
        self.assertTrue(any("still present as a current proposal" in error for error in errors), errors)
        self.assertTrue(validate_contract(terminal_left_active))

    def test_explicit_review_cannot_apply_an_expired_proposal(self):
        receipt = load_json(FIXTURES / "must_accept" / "applied_receipt_explicit_full_block.json")
        receipt["explicitReviewProof"]["proposal"]["expiresAt"] = "2026-08-01T08:09:30Z"
        errors = receipt_time_order(receipt)
        self.assertTrue(any("expired at evaluation" in error for error in errors), errors)
        self.assertTrue(validate_contract(receipt))

    def test_applied_revision_strictly_advances_base_revision(self):
        receipt = load_json(FIXTURES / "must_accept" / "applied_receipt_explicit_full_block.json")
        for applied_revision in ("ctx_40_cccccccc", "ctx_41_bbbbbbbb"):
            with self.subTest(applied_revision=applied_revision):
                candidate = copy.deepcopy(receipt)
                candidate["appliedRevision"] = applied_revision
                errors = receipt_time_order(candidate)
                self.assertTrue(any("advance beyond" in error for error in errors), errors)
                self.assertTrue(validate_contract(candidate))

    def test_planning_context_rejects_future_nested_records(self):
        proposal = load_json(FIXTURES / "must_accept" / "proposal_full_block_explicit.json")
        receipt = load_json(FIXTURES / "must_accept" / "applied_receipt_explicit_full_block.json")
        future_proposal = self._planning_context_with_current_proposal(
            proposal, "2026-08-01T08:03:00Z"
        )
        future_proposal["generatedAt"] = "2026-08-01T08:01:00Z"
        self.assertTrue(planning_context_integrity(future_proposal))

        future_receipt = self._planning_context_with_application(
            proposal, receipt, "2026-08-01T08:12:00Z"
        )
        future_receipt["generatedAt"] = "2026-08-01T08:11:00Z"
        self.assertTrue(planning_context_integrity(future_receipt))

    def test_result_id_binds_the_full_proposal_envelope(self):
        invariant_ids = {item["id"] for item in SCHEMA["x-t4l-invariants"]}
        self.assertIn("proposal-result-idempotency-v1", invariant_ids)
        proposal = load_json(FIXTURES / "must_accept" / "proposal_full_block_explicit.json")
        self.assertEqual(proposal_idempotency_errors([proposal, copy.deepcopy(proposal)]), [])
        changed = copy.deepcopy(proposal)
        changed["expiresAt"] = "2026-08-01T12:30:00Z"
        self.assertTrue(proposal_idempotency_errors([proposal, changed]))


if __name__ == "__main__":
    unittest.main()
