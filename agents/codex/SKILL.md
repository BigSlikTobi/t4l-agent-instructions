# T4L Self-Hosted Server

Use this skill when starting a T4L Trainer coaching session through the
self-hosted T4L server and MCP tools.

## Required startup

1. Read `docs/exchange_contract.md`, `docs/freshness_rules.md`, and
   `docs/coaching_workflow.md` from this repo.
2. Verify `t4l-server` is installed:
   ```bash
   command -v t4l-server
   ```
3. If missing, ask the user before installing the official local package.
4. Start the server:
   ```bash
   t4l-server serve --data-dir ~/T4LServerData
   ```
5. Ask the user to enter the printed Server URL and API key in the app Settings
   screen, then migrate or push fresh context.
6. Connect to the printed MCP URL using the same API key.
7. Do not coach until `get_day_context` returns fresh context.

## Boundaries

- Do not generate server code.
- Do not modify unrelated files or shell profiles.
- Use the MCP tools as the source of truth for the session.
