# Exchange Contract

The app and agent communicate through the self-hosted T4L server. The app uses
semantic REST endpoints. Agents use MCP tools. The server stores JSON payloads
in SQLite and does not own accepted training state.

## App uploads through REST

- `PUT /v1/app/snapshot`
- `PUT /v1/context/day`
- `PUT /v1/context/daily-snapshot`
- `PUT /v1/profile`
- compatibility `/files/{name}` endpoints during migration

## Agent results through MCP

- `write_training_block_plan`
- `write_fuel_guidance`
- `write_nutrition_analysis_result`

The app imports pending results only after user confirmation where needed.
