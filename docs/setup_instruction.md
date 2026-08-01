# Setup Instruction

Read this file first when starting a T4L Trainer agent session.

## Reading Order

1. Read `docs/initial_setup.md`
   - Install or verify `t4l-server`.
   - Start or verify the self-hosted server.
   - Give the user the Server URL and API key.
   - Connect the app to the server.
   - Connect the agent to MCP.
   - Install the coaching skills into your harness (if it supports skills) so
     future sessions load them automatically — the user does not do this by hand.
   - Finish with a full gateway restart **when something changed** (e.g. skills
     were just installed) so the skills load; then verify the server, MCP, and
     skills are up. Skip the restart if everything is already loaded and running.
   - Wait for fresh app context before coaching.

2. Read `docs/coaching_setup.md`
   - Inspect the synced phone context.
   - Run first-run goal discovery when needed.
   - Establish the Coaching Contract.
   - Use memory wiki, training logs, nutrition logs, and HealthKit context.
   - Compare the candidate session and coaching copy with recent context; keep
     progression anchors stable while adding safe, useful variety.
   - Decide today's coaching action.
   - Write app-consumed results only through MCP tools.
   - Answer the in-app chat channel (`get_pending_chat_messages` /
     `write_chat_reply`), and schedule the answer routine so chat stays live.

3. Read `docs/exchange_contract.md` before writing app-consumed JSON
   - Use the current result shapes and mobile display fields.
   - Keep training plans compatible with the phone import validator.

4. Read `docs/journal.md` for recent contract changes
   - Adopt new capabilities (tracking modes, daily coaching context, fuel
     round-trip) immediately.
   - Entries are dated — skim for anything newer than your last session.

## Session Rule

Setup and coaching are separate phases. Complete the initial setup first. End
setup with a full gateway restart whenever something changed (so newly installed
skills load), then verify the server, MCP, and skills are up — but never restart
unconditionally, or you will loop. Start coaching only after the app has
connected to the server and `get_day_context` returns fresh context for the
current session.
