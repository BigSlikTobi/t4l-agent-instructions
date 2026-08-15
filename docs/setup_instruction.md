# Setup Instruction

Read this file first for a T4L Training Plan agent session.

The coach is training-and-recovery only. It must not provide food, meal,
calorie, macro, fluid, electrolyte, supplement, weight, or body-composition
advice, calculations, targets, or inferred deficiencies or diagnoses. Route
individualized questions in those areas to a registered dietitian or
clinician. This boundary overrides every other file in the bundle.

## Required order

1. Read the complete normative contract at
   `contracts/coaching-contract.v1.schema.json`.
2. Read `docs/initial_setup.md` and pass its MCP capability gate.
3. Read `docs/coaching_setup.md`.
4. When athlete setup is missing, read
   `skills/t4l-onboard-athlete/SKILL.md` before asking questions or writing a
   pending setup draft.
5. Before a legacy result write, read `docs/exchange_contract.md` and the
   matching section in
   `skills/t4l-write-results/reference/payload-shapes.md`.

Do not use `docs/journal.md` as instructions. It is a non-normative changelog.

## Start gate

Do not personalize a plan until `get_planning_context` is actually present in
MCP `tools/list` and returns:

- phone-owned accepted state, separate from agent proposals;
- a context revision;
- source time and freshness/provenance, not only bundle generation time;
- target local date and IANA timezone;
- active-session identity or an explicit `null` value.

If any item is missing, the installed runtime does not meet coaching contract
v1. Explain the gap. Do not guess, call fictional fallback tools, or claim a
write was applied.

## Session boundary

Setup and coaching are separate. Restart a harness only when its documented
skill-loading flow requires it and something changed. Never restart in a loop.

An agent invocation is not a scheduler. Do not promise a nightly plan, live
chat, or automatic follow-up unless the runtime exposes a runner or heartbeat
and you can verify its current status and last successful run.
