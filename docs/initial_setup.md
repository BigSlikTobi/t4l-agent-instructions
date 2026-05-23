# Initial Setup

Use this guide for the one-time or per-session connection setup between the
agent, the self-hosted T4L server, and the T4L Trainer app.

## Server Setup

1. Verify `t4l-server` is installed:
   ```bash
   command -v t4l-server
   ```
2. If the server is missing, ask the user before installing it:
   ```bash
   pipx install t4l-server
   ```
3. Start the server if it is not already running:
   ```bash
   t4l-server serve --data-dir ~/T4LServerData
   ```
4. Give the user the printed Server URL and API key so they can enter them in
   the T4L Trainer Settings screen.
5. Connect to the printed MCP URL with the same API key.
6. Wait until the user connects the app and migrates or pushes fresh context.
   Do not coach from memory alone.

## Source Of Truth

Use MCP tools as the source of truth for the session. Treat `get_day_context`
as the primary current-day context. Use `get_app_snapshot`, `get_profile`, and
`get_pending_requests` as supporting context.

Inspect the available context before coaching:

- `day_context`: primary current-day context.
- `daily_snapshot`: compact latest app snapshot when present.
- `app_snapshot`: full phone migration/sync payload when present.
- `profile`: athlete profile, goals, equipment, schedule, constraints, and
  preferences.
- `activeBlock`: current accepted training block.
- `nextWorkout`: next planned workout.
- recent training logs and latest workout log.
- recent nutrition logs and latest nutrition entry.
- HealthKit activity summaries and activity sessions.
- active `memoryWiki` entries.
- pending requests such as training block, fuel guidance, or nutrition analysis.

Missing files, missing metrics, missing HealthKit permissions, or absent logs
are unknown, not zero. If `day_context` is missing or stale, ask the user to
open the app and push fresh context before coaching.
