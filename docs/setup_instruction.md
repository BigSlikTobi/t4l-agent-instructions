# Setup Instruction

Read this file first when starting a T4L Trainer agent session.

## Reading Order

1. Read `docs/initial_setup.md`
   - Install or verify `t4l-server`.
   - Start or verify the self-hosted server.
   - Give the user the Server URL and API key.
   - Connect the app to the server.
   - Connect the agent to MCP.
   - Wait for fresh app context before coaching.

2. Read `docs/coaching_setup.md`
   - Inspect the synced phone context.
   - Run first-run goal discovery when needed.
   - Establish the Coaching Contract.
   - Use memory wiki, training logs, nutrition logs, and HealthKit context.
   - Decide today's coaching action.
   - Write app-consumed results only through MCP tools.

3. Read `docs/exchange_contract.md` before writing app-consumed JSON
   - Use the current result shapes and mobile display fields.
   - Keep training plans compatible with the phone import validator.

4. Read `docs/journal.md` for recent contract changes
   - Adopt new capabilities (tracking modes, daily coaching context, fuel
     round-trip) immediately.
   - Entries are dated — skim for anything newer than your last session.

## Session Rule

Setup and coaching are separate phases. Complete the initial setup first. Start
coaching only after the app has connected to the server and `get_day_context`
returns fresh context for the current session.
