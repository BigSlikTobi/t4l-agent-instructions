# T4L Agent Instructions

Shared startup and coaching instructions for T4L Trainer agents. This repo is
the canonical agent bootstrap source.

These docs are agent adapters only; the self-hosted server implementation lives
in the installed `t4l-local-bridge` package and is started with `t4l-server`.

## Startup rule

Do not coach from memory alone. Start or verify the self-hosted T4L server,
connect through MCP, wait for fresh app context, inspect the available tools and
context, then begin the training workflow.

## Repos

- Server package: `/Users/tobiaslatta/Projects/temp/t4l-local-bridge`
- This instruction repo: `/Users/tobiaslatta/Projects/temp/t4l-agent-instructions`
