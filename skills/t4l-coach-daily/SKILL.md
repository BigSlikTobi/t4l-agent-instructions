---
name: t4l-coach-daily
description: Use for a T4L daily coaching decision from fresh, phone-accepted planning context. Produces a proposal, never an apply claim.
---

# T4L Daily Coaching

Requires `../../contracts/coaching-contract.v1.schema.json`. The full procedure
is in `../../docs/coaching_setup.md`; this skill is the short execution adapter.

## Run

1. Call `get_planning_context` immediately before planning.
2. Stop if accepted state, provenance, source time, freshness, target
   date/timezone, context revision, or active-session identity is missing.
3. Select the matching phone-authored current request and keep its `requestId`.
   If none exists, discuss a draft; do not invent an ID or emit a contract
   proposal.
4. Keep phone-accepted state separate from current proposals and
   receipt-embedded proposal history. Do not treat a latest result slot as
   accepted because it is named `activeBlock` or `nextDayPlan`.
5. Separate facts from unknowns. Use only data present in the planning context.
   Do not call guessed snapshot, profile, memory, HealthKit, or live-set tools.
6. Decide `progress`, `hold`, `substitute`, `deload`, or `rest` from accepted
   goals, constraints, logs, recovery, and requests.
7. Keep accepted anchors. Change a training lever only when evidence or an
   explicit request supports it. Variety is not a quota.
8. Choose flat work, a two-exercise `superset`, a three-or-more-exercise
   `circuit`, or a safe mix from the session goal. Use `circuit`, never
   `circle`, in JSON. Do not group work when it harms technique, loading, rest,
   or safety. In groups, `rounds` repeats the full group; child `sets` is `1`
   or omitted. Child rest is after a non-final child before the next child, not
   between sets. Group rest is after the final child of each round.
9. Give every planned exercise, including group children, a verified canonical
   `https://www.youtube.com/shorts/<videoId>` `explainerUrl` plus setup, cues,
   and common mistakes. Other video/page URLs are invalid. Never invent a URL
   or video ID. If the runtime cannot verify a suitable Short, do not write the
   plan.
10. Explain observed recovery facts against the athlete's personal baseline.
    Never turn those signals into nutrition, hydration, supplement, weight, or
    body-composition guidance or inferred diagnoses.
11. Classify the proposal. Full blocks and material daily changes require
   explicit review. Minor daily changes or guidance can be automatic candidates
   only when every consent/revision/date/expiry/session check in the contract
   passes.
12. Record every relied-on accepted-state field in fresh `inputSources`.
13. Use `t4l-write-results` to validate and store the legacy body.
14. Say “proposal stored; review and application unconfirmed.” Say “applied”
    only after a matching phone applied receipt.

## Hard limits

- The coach is training-and-recovery only. Refer individualized nutrition,
  hydration, supplement, weight, and body-composition questions to a registered
  dietitian or clinician.
- No live mid-set claim without a fresh, phone-sourced set event.
- No nightly-plan promise without a verified runner/heartbeat.
- A coaching intent stays unfulfilled after a write. Close it only after
  proposal-matched apply proof.
