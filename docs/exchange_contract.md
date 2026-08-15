# Exchange Adapter

This file explains how current MCP transport maps to the T4L coaching contract.
It is not a second contract.

The only normative source is:

`contracts/coaching-contract.v1.schema.json`

Legacy result body shapes live in:

`skills/t4l-write-results/reference/payload-shapes.md`

## Capability discovery

Read MCP `tools/list` at runtime. Do not infer tools from the server executable,
a journal entry, or this list.

Personalized coaching requires a provenance-rich `get_planning_context`. The
instruction layer does not allow direct snapshot, daily-snapshot, profile,
memory, HealthKit, or live-set fallbacks.

When advertised, legacy proposal writers are:

- `write_athlete_setup_draft`
- `write_training_block_plan`
- `write_next_day_plan`

Nutrition and fuel readers and writers are intentionally outside the coaching
surface, including when an old server still stores those legacy artifact kinds.

`write_athlete_setup_draft` transports a strict confirmed onboarding draft. It
writes pending result kind `athlete_setup_draft` with payload schema
`athlete_setup_draft.v1`. It is not accepted state. The phone alone can
accept it and expose that decision through a fresh `contextRevision`.

When advertised, legacy chat tools are:

- `get_pending_chat_messages`
- `write_chat_reply`

An auxiliary read may be used only when it is present in `tools/list`, the
planning context references the exact object, and its response carries usable
provenance. Do not turn an optional auxiliary tool into a required fictional
workflow.

## Planning-context mapping

The planning tool must expose the `planning_context` branch of coaching
contract v1. Its `acceptedState` must satisfy the phone-owned `accepted_state`
branch.

Standard JSON Schema validators ignore the contract's `x-t4l-invariants`
annotations. A compatible app, server, or runtime must enforce those semantic
rules too. The golden corpus under `tests/fixtures/coaching_contract/` exercises
them but does not replace the normative schema.

At minimum it must keep these apart:

- phone-owned accepted state;
- current/open agent proposals;
- applied receipts with their embedded proposal history;
- open requests in `currentRequests`;
- consumed, rejected, and expired records in `requestHistory`.

Each accepted source needs its own source time, freshness, and revision. A
bundle `generatedAt` only tells when the server assembled the response.

Old `planning_context.v1` responses can place the latest agent result in fields
named `activeBlock` or `nextDayPlan`. Those fields are proposal history unless
phone provenance and an accepted revision prove otherwise. Legacy fuel and
nutrition fields must be removed before the context reaches the model.

If the mapping is absent, stop personalized/state-changing coaching and report
the compatibility gap.

## Proposal writes

The agent creates proposals only. Contract-v1 delivery requires a writer whose
declared arguments accept the full `proposal` envelope and whose response keeps
its request ID, result ID, digest, base revision, target, change class, review,
and expiry.

Do not add envelope fields to a writer that does not accept them. A legacy raw
body write is non-contract storage. It cannot support correlation, safe retry,
automatic apply, or a matching applied receipt. Treat it as manual-only and
application-unconfirmable.

Every contract-v1 proposal answers one phone-authored `currentRequest` and must
echo its `requestId`. Never invent that ID. Without a matching current request,
the agent may discuss a draft but cannot emit a contract-v1 proposal.

A legacy write response proves broker storage at most. It does not prove:

- phone import;
- athlete review;
- application;
- a new accepted revision.

Do not invent a request status. Keep the coaching intent unfulfilled after the
write. Fulfil it only when the phone returns a matching applied receipt. A later
revision or similar-looking state is not proposal-correlated proof.

### Retry identity

Retry the same logical proposal only with the same `requestId`, `resultId`,
payload digest, and byte-for-byte same canonical full proposal envelope. Any
changed field — including target, base revision, source dependency, expiry,
review, or payload — needs a new `resultId`. Reusing a `resultId` with a changed
envelope is a conflict.

Legacy writers do not expose this idempotency contract. After an ambiguous
timeout, do not blindly send the proposal again. Re-read current proposal and
accepted-state evidence. If the outcome is still unclear, tell the athlete or
operator that delivery is unknown.

## Review and apply

The schema has the exact review and consent conditionals.

- Full blocks and material daily changes stay review-required.
- Every apply mode rejects a proposal at or after its `expiresAt`.
- Standing consent is valid only when it comes from accepted phone state, is
  unexpired, and covers the exact proposal scope.
- Automatic apply also needs the same target date/timezone, matching base
  revision and no active-session conflict.
- A broker write response is never an applied receipt.

Current legacy tools do not prove review or automatic apply. Their raw stored
bodies are non-contract and manual-only.

## Chat sequencing

Pending queue order is not ownership. A worker may reply only to a turn it owns.

### With claim support

Use concurrent workers only when `tools/list` exposes an atomic claim/lease and
idempotent reply contract. Keep the claimed message text, conversation ID,
message sequence/ID, claim ID, and claim expiry together for the whole job.

Before a write, verify the claim is still valid. Bind the write to that exact
message and its idempotency key. Never move to a newer athlete message because
it arrived while work was running.

### Legacy single-worker mode

If the runtime only exposes `get_pending_chat_messages` and `write_chat_reply`:

1. Prove one exclusive consumer for the conversation through a single
   deployment or external lock. If that cannot be proved, do not write chat.
2. Select the oldest pending athlete message.
3. Copy its content, conversation ID, and `seq` into the job.
4. Read a fresh `get_planning_context` for answer context.
5. Call `write_chat_reply` with the original `seq` as `inReplyToSeq`.
6. Repeat for the next pending message.

Never omit `inReplyToSeq`. An unscoped legacy reply can acknowledge unrelated
newer messages. Polling is not idempotent, so overlapping processes or workers
can duplicate replies. A written instruction saying “one worker” is not a lock.

### Escalation

An escalation acknowledgement and its final answer belong to the same claimed
athlete message. Pass the captured message and all IDs directly to the heavy
worker. Do not re-poll to rediscover the question. Bind both writes to the same
original sequence/claim.

An acknowledgement is not completion. If durable claim/processing state is not
available, a crash can strand the turn. Say this honestly. On an ambiguous
write, inspect current chat evidence before retrying. Without an idempotency
key, do not blindly post again.

Never acknowledge, close, or answer a newer unrelated message as part of the
older job.

## Compatibility policy

| Layer | Contract v1 responsibility |
|---|---|
| Phone app | Own accepted state, review decisions, standing consent, conflict checks, and applied receipts. |
| Server | Preserve provenance/status, revisions, identity, idempotency, claims, and receipts without relabeling proposals as accepted. |
| Agent runtime | Discover tools, bind chat work, expose runner health, and pass contract fields unchanged. |
| Instructions | Read supported accepted state, create proposals, and make claims no stronger than returned evidence. |

Version rules:

- `coaching-contract.v1.schema.json` is exact version `1.0.0`. Do not assume a
  different patch or minor version is compatible.
- Any contract change gets a new advertised exact version and schema artifact.
  A breaking semantic change also requires a new major version.
- During migration, layers may advertise more than one exact supported version.
- Instructions must reject any unadvertised exact version for state-changing
  work.
- App, server, runtime, and instructions should advertise exact supported
  contract versions during capability negotiation.
- Legacy payload schemas such as `next_day_plan.v1`, REST `/v1`, server semver,
  and watch payload versions are separate version axes. They do not prove
  coaching contract v1 support.

## Known runtime requirements

These are requirements, not claims about shipped behavior:

- provenance-rich accepted state in `get_planning_context`;
- current proposals separate from accepted state, with applied proposal history
  preserved inside app-authored receipts;
- context, base, and applied revisions;
- app-authored applied receipts;
- request/result idempotency and payload-digest conflict checks;
- atomic chat claim/lease plus reply idempotency;
- runner or heartbeat status for nightly/background claims.

Until each capability appears in `tools/list` and the returned schema, use the
safe legacy behavior above.
