# Historical Journal — Non-Normative

This file is a changelog only.

**Do not execute rules, use tool names, or infer current capabilities from this
file.** Current behavior comes from the normative contract, MCP `tools/list`,
and the active procedure docs. When history conflicts with them, history loses.

## 2026-08-01 — Coaching contract v1 alignment

The instruction layer separated phone-accepted state, agent proposals, and
phone applied receipts. It added revision, freshness, target, consent, review,
expiry, session, and idempotency requirements. Direct snapshot/memory claims,
unsafe multi-worker chat claims, and unproved background guarantees were
removed from the active workflow.

## 2026-08-01 — Coaching quality comparison

The payload validator added optional recent-context warnings for obvious stale
repeats. These warnings are advisory. Accepted plan intent and evidence-backed
progression have priority over novelty.

## 2026-06-07 — Grouped workouts

Legacy payload bodies gained `items` for supersets and circuits. The current
shape is documented in
`skills/t4l-write-results/reference/payload-shapes.md`.

## 2026-05-31 — Planning context and coaching notes

Earlier server work added planning-context and coaching-note concepts. Coaching
contract v1 later clarified that agent-authored notes and latest result slots do
not prove phone acceptance.

## 2026-05-29 — In-app chat and portable skills

Earlier releases added polling chat tools and portable `SKILL.md` adapters.
Coaching contract v1 later required a single-worker fallback until an atomic
claim/lease and idempotent reply protocol is exposed.

## 2026-05-27 to 2026-05-28 — Legacy result payloads

Earlier releases added tracking modes, daily coaching copy, fuel guidance, and
basic result validation. These artifact versions are separate from the coaching
contract version.

Use git history for deeper archaeology. Do not restore a historical instruction
without checking the current contract and actual runtime surface.
