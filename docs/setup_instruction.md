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

## Session Rule

Setup and coaching are separate phases. Complete the initial setup first. Start
coaching only after the app has connected to the server and `get_day_context`
returns fresh context for the current session.
