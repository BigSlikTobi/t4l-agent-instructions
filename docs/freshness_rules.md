# Freshness Rules

- Treat MCP `get_day_context` as the primary current-day context.
- Do not coach until a fresh app sync has happened in the current session.
- Missing HealthKit, nutrition, or workout fields are unknown, not zero.
- If context is stale or server sync fails, ask the user to open the app,
  reconnect the server, and push fresh context.
