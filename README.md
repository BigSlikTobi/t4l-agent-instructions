# T4L Agent Instructions

Shared startup and coaching instructions for T4L Trainer agents. This repo is
the canonical agent bootstrap source.

These docs are agent adapters only; the self-hosted server implementation lives
in the installed `t4l-server` package and is started with `t4l-server`.

## Startup rule

Read `docs/setup_instruction.md` first. It routes agents through the one-time
initial setup docs and then the coaching setup docs.

Do not coach from memory alone. Start or verify the self-hosted T4L server,
connect through MCP, wait for fresh app context, inspect the available tools and
context, then begin the training workflow.

## Docs

- `docs/setup_instruction.md`: first-read sitemap for agents.
- `docs/initial_setup.md`: server, app, and MCP initialization.
- `docs/coaching_setup.md`: goal discovery, safe novelty and variety, coaching
  rules, nutrition guidance, and MCP result writes.
- `docs/exchange_contract.md`: REST and MCP exchange contract.
- `docs/freshness_rules.md`: freshness and missing-data rules.

## References

- Server package: `t4l-server`
- This instruction repo: `https://github.com/BigSlikTobi/t4l-agent-instructions`
