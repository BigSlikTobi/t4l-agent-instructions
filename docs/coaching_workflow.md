# Coaching Workflow

1. Verify `t4l-server` is installed.
2. If the server is missing, ask the user before installing it with:
   ```bash
   pipx install t4l-server
   ```
3. Start the server if it is not running:
   ```bash
   t4l-server serve --data-dir ~/T4LServerData
   ```
4. Give the user the printed Server URL and API key so they can enter them in
   the app Settings screen.
5. Connect to the printed MCP URL with the same API key.
6. Wait for the app to migrate or push fresh context. Do not coach from memory
   alone. If `day_context` is missing or stale, ask the user to push fresh
   context.
7. Use MCP tools to inspect `day_context`, `app_snapshot`, `profile`, pending
   requests, active block, next workout, recent logs, nutrition, HealthKit
   summaries, and memory wiki.
8. If the long-term goal or current short-term block target is unclear, run goal
   discovery before writing a plan. Clarify block target, length, success
   criteria, schedule, equipment, constraints, nutrition context, and
   preferences.
9. Separate facts from assumptions.
10. Decide whether today's training should progress, hold, substitute, deload,
   or rest.
11. Give concise food-based nutrition guidance. Use recent nutrition as a soft
    readiness signal, not as fixed targets unless the user asks for targets.
12. Ask before changing goals, ignoring constraints, or writing app-consumed
    JSON.
13. Write result JSON only through MCP tools when the user needs the app to
    import something.
