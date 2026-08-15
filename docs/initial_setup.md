# Initial Setup

Use this once to connect the agent, self-hosted server, and T4L app. The server
and app are separate products. These instructions cannot add missing runtime
behavior.

## 1. Connect

1. Use the agent runtime and model the customer already configured. Do not
   choose, switch, download, or call a model provider from these instructions.
2. The OpenClaw owner installs the exact pinned `t4l-connect` bootstrap package
   through the OpenClaw Control UI or host CLI. This is the only manual software
   approval. Do not ask the model to install it from chat.
3. The bootstrap accepts only its release-built policy. That policy pins a
   signed release manifest at an HTTPS URL, its SHA-256, signing key, release identity, and
   every artifact digest. Repository URLs and commits are source metadata, not
   executable install instructions. Never clone or install a mutable branch.
4. The athlete enters only the reachable trusted HTTPS OpenClaw address in the
   app. The app creates its device key and one pending pairing code. A local
   install must already be reachable through trusted HTTPS, such as Tailscale
   Serve; there is no T4L relay fallback.
5. The athlete sends `/t4l connect XXXX-XXXX` through an already authenticated
   owner channel. The runtime adapter must handle this before model input and
   bind the verified channel, account, and sender identity to that phone request.
6. Deterministic bootstrap code installs one isolated server and instruction
   bundle, generates host-only credentials, configures MCP and service startup,
   verifies chat and coaching capabilities, and adopts the original phone
   request. It must resume safely or roll back on failure.
7. The phone proves possession of its key, receives only the exact `chat`,
   `sync`, and `status` scopes, then asks the verified coach to begin athlete
   onboarding. Ask the app to sync current phone state.

Never request or place a provider key, runtime administrator credential, MCP
key, SSH credential, or connector runtime token on the phone. The legacy manual
URL/API-key path is an advanced compatibility path, not normal onboarding.

The model does not choose releases, URLs, commands, ports, service files,
credentials, or rollback actions. Those are host-installer decisions. If the
signed policy is missing or verification fails, stop and report that setup is
not ready.

Command existence is not a capability check. A stale server can start cleanly
while exposing the wrong MCP surface.

## 2. Discover the real MCP surface

Use MCP initialization and `tools/list`. Never copy a tool name from an old
journal entry or assume it exists from a package version.

Personalized coaching requires `get_planning_context`. Its response must meet
the `planning_context` branch of
`contracts/coaching-contract.v1.schema.json`. Its `acceptedState` must meet the
phone-owned `accepted_state` branch with all provenance and state-boundary
fields.

For the workflow being run, also verify the named write or chat tool is present.
Current adapter names can include:

- `write_training_block_plan`
- `write_next_day_plan`
- `get_pending_chat_messages`
- `write_chat_reply`

Nutrition and fuel read/write tools are outside the coach scope and must not be
advertised or called.

This list is not proof. `tools/list` is proof. Never instruct the model to call
direct snapshot, profile, memory, HealthKit, daily-snapshot, or live-set tools.
This instruction layer has no contract for them. Accepted athlete data comes
through the planning context.

## 3. Validate the planning context

Read `get_planning_context` once after sync. Check:

- the exact contract version is advertised and supported;
- the phone-owned accepted state is clearly marked;
- `contextRevision` is present;
- every coaching fact has usable provenance, including `sourceTime` and
  freshness status;
- `target.localDate` and `target.timeZone` are present;
- `activeSessionId` is present or explicitly `null`;
- proposals are not presented as the accepted block or accepted day plan;
- `currentRequests` contains only unexpired `pending` or `in_review` records;
- consumed, rejected, and expired records stay terminal in `requestHistory`.

A bundle-level `generatedAt` says when the server assembled JSON. It does not
say when the phone measured or accepted a fact.

If the response fails these checks, stop personalized/state-changing coaching.
The safe response is to name the missing contract support and ask for a
compatible runtime or a fresh app sync. Do not stitch together fictional
fallback reads.

## 4. Chat concurrency gate

`get_pending_chat_messages` is a queue read, not an atomic claim, unless the
tool schema explicitly returns a claim/lease token and expiry.

- With atomic claim and idempotent reply support, workers may run concurrently.
- Without both, chat writes require one externally serialized consumer for that
  conversation, backed by a single deployment or an external lock.
- If exclusive ownership cannot be proved, do not poll and write chat replies.
- Never describe polling alone as safe from duplicate replies.

See `skills/t4l-answer-chat/SKILL.md` for turn sequencing.

## 5. Runner gate

Only claim background or nightly operation when an advertised runtime runner or
heartbeat shows all of these:

- enabled job identity;
- expected cadence and timezone;
- last successful run;
- current health or next scheduled run.

Without that evidence, say the agent runs only when invoked. A loop example in
documentation is not a deployed runner.

## 6. Install portable skills when supported

If the harness supports `SKILL.md`, keep this repo layout intact. Register its
`skills/` directory as a skill source, or symlink the four skill folders from
this checkout into the harness's documented skills directory. Refresh an
existing link instead of creating duplicates.

Do not copy a skill folder by itself. Each adapter depends on the one contract
under `contracts/` and procedure docs under `docs/`. If the harness cannot use
links or external skill sources, copy the whole repo while preserving those
relative paths.

Restart only if that harness loads skills at startup and files changed.

The skills are adapters. They do not relax the capability gate or replace the
normative contract.
