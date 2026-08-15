---
name: t4l-write-results
description: Use before a T4L MCP result write. Validates and stores a legacy proposal body without claiming phone review or application.
---

# Write T4L Proposals Safely

Read `../../contracts/coaching-contract.v1.schema.json` first. The agent writes a
proposal. A tool success is a broker storage result, not an applied receipt.

## Capability check

Use only a writer present in MCP `tools/list`:

| Proposal body | Legacy writer |
|---|---|
| Confirmed athlete setup draft | `write_athlete_setup_draft` |
| Full training block | `write_training_block_plan` |
| Single day | `write_next_day_plan` |

Nutrition and fuel readers or writers are not part of the coaching tool set.
Never call a legacy nutrition or fuel tool even if an outdated runtime exposes
one.

Do not call a missing tool. Do not add the coaching-contract envelope to a tool
whose declared arguments accept only a legacy payload body.

`write_athlete_setup_draft` is a specialized onboarding writer, not proof of a
phone-owned profile update. Call it only after the athlete confirms the exact
chat summary and only with strict `athlete_setup_draft.v1` from
`../t4l-onboard-athlete/SKILL.md`. Its pending result kind is
`athlete_setup_draft`. A successful write means pending phone review; it is not accepted state and must never be reported as accepted, synced, or applied.

A writer is contract-v1 capable only if it accepts the full `proposal` envelope
and preserves all IDs, digest, revision, target, review, and expiry fields. A
raw legacy body write is non-contract, manual-only, and cannot yield a
correlatable applied receipt.

## Review classification

- A full block is always review-required.
- A material daily change is always review-required. This includes changes to
  goals, hard constraints, training direction, material training stress,
  or rest-versus-train.
- Every proposal must still be unexpired when reviewed and applied. An expired
  proposal needs a new `resultId` and a fresh envelope.
- Only minor daily changes or guidance can be automatic candidates.
- Automatic apply still needs phone-accepted standing consent for the exact
  scope, matching target date/timezone and base revision, and no active-session
  conflict.
- If the runtime cannot prove every check, require explicit review. A legacy
  storage response does not prove that review is queued.

## Identity and retry

Every contract-v1 proposal must echo the matching phone-authored `requestId`.
Never invent it. Generate one `resultId` for the logical proposal and keep it
plus the payload digest and full canonical proposal envelope stable across
retries. Any changed field needs a new `resultId`.

Legacy writers may not accept these fields or enforce idempotency. They are a
degraded, non-contract adapter. Follow their declared schema. After an ambiguous
timeout, inspect current context before any retry. Never assume that sending
twice is safe.

## Training payload quality gate

Apply this gate to every `training_block_plan` and `next_day_plan` before the
legacy-body validator:

- Choose structure deliberately. Use flat exercises for heavy, technical,
  rehab, or full-rest work; a `superset` for exactly two compatible exercises;
  a `circuit` for three or more safe exercises; and mixed `items` when needed.
- The JSON term is `circuit`, never `circle`. Supersets alternate A1, B1, A2,
  B2. Do not nest groups or group exercises when that harms technique, loading,
  rest, or safety.
- In a group, `rounds` repeats the full child sequence and is the only repeat
  source. Child `sets` is `1` or omitted. Child `restSeconds` applies after a
  non-final child before the next child step; it is not rest between sets.
  Group `restSeconds` applies after the final child of every round.
- Every exercise, including every group child, needs nested `media` with a
  verified canonical `https://www.youtube.com/shorts/<videoId>`
  `explainerUrl`, non-empty `setup`, `cues`, and `commonMistakes`. Normal
  YouTube watch links, `youtu.be`, other video hosts, and web pages are invalid.
- Verify that each Short shows the exact exercise variation during the current
  run or use a trusted, current catalog from accepted context. A verified
  YouTube result may supply the ID, but store the canonical `/shorts/` form.
  Never fabricate a URL or video ID. If no available capability can verify the
  Short, do not write the plan; report the missing capability.
- A full block must include at least one workout for every declared week.
  `weeklyFocus` and `measurableTargets` are non-empty arrays of strings.

## Validate the legacy body

Read `reference/payload-shapes.md`, then run:

```bash
python3 scripts/validate_payload.py <kind> path/to/payload.json
```

Kinds used by the coach are `training_block_plan` and `next_day_plan`.

For an advisory comparison against accepted recent context:

```bash
python3 scripts/validate_payload.py next_day_plan plan.json \
  --recent-context accepted-comparison.json
```

Use only phone-accepted logs and applied plan history in that comparison file.
Do not include pending/rejected proposals or persist sensitive data for the
check. Fix every `ERROR`. Review each `WARN`; it is not an order to add novelty.

## Store and report

Call the writer once. If it confirms storage, say “proposal stored; review and
application unconfirmed.” For a raw legacy writer, add “This is non-contract,
manual-only storage.” Do not say the plan or target was accepted,
queued for review, imported, scheduled, or applied unless the returned evidence
proves that exact state.

Keep the coaching intent unfulfilled. Close it only after a matching phone
applied receipt. A later revision or similar-looking state is not correlated
proof. If the receipt is absent, say application cannot be confirmed.
