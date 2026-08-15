# T4L Agent Instructions

This repo is the instruction layer for the T4L Training Plan agent. It does not
implement the phone app, server, MCP runtime, or a background runner.

## Source precedence

Start a session with `docs/setup_instruction.md`. When sources disagree, use
this precedence:

1. `contracts/coaching-contract.v1.schema.json` — the only normative coaching
   contract. It defines phone-accepted state, agent proposals, applied receipts,
   revisions, freshness, consent, review, and retry identity.
2. `docs/setup_instruction.md` and `docs/coaching_setup.md` — startup and
   coaching procedures.
3. `skills/t4l-write-results/reference/payload-shapes.md` — current legacy MCP
   payload bodies. These shapes do not prove that a proposal was applied.

The files under `skills/` and `agents/` are adapters. They must point back to
the contract. They must not redefine it. `docs/journal.md` is history only and
is never an instruction source.

## Runtime neutrality

Use whatever agent runtime and model the customer configured. This repo has no
provider or model default and makes no direct provider API call. It never asks
for provider credentials. Optional provider/model/reasoning descriptor fields
may be repeated in the coach introduction when known; they are display metadata
only and never a trust or capability gate.

## Core boundary

Personalized coaching starts from a fresh, provenance-rich
`get_planning_context` response. A server timestamp alone is not provenance.
An agent result is a proposal. It becomes accepted phone state only after the
phone emits a matching applied receipt. A later revision or similar-looking
state is not proof of which proposal was applied.

Do not fall back to guessed snapshot, memory, HealthKit, or live-workout tools.
Use only tools returned by MCP `tools/list`. If the required planning contract
is missing, say so and stop the state-changing workflow.

## Verification

Run:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

## Related runtime

The server is distributed separately as `t4l-server`. Contract support must be
verified through MCP capability discovery, not from command existence or an
assumed package version.

OpenClaw installation starts with one owner-approved, version-pinned
`t4l-connect` bootstrap package. After that approval, deterministic host code
verifies a signed release manifest, installs the isolated connector, configures
MCP, and rolls back failed changes. The model never installs from repository
branches and never receives host, runtime, MCP, or provider credentials.
