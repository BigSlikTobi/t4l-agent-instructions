# T4L Agent Skills

Portable [Agent Skills](https://agentskills.io) for T4L Trainer coaching agents.
These are the on-demand, procedural layer that sits on top of the bootstrap docs
in this repo. They follow the open `SKILL.md` convention, so they work under any
skills-compatible harness (Claude Code, Codex CLI, Gemini CLI, OpenCode,
OpenClaw, Hermes, …) driving any sufficiently capable LLM: the **harness** does
discovery, progressive disclosure, and (optional) script execution — the model
only judges relevance from each skill's `description`.

## Skills

| Skill | Use when |
|---|---|
| [`t4l-onboard-athlete`](t4l-onboard-athlete/SKILL.md) | the long-term goal or current block target is missing/unclear — runs goal discovery and produces a Coaching Contract |
| [`t4l-coach-daily`](t4l-coach-daily/SKILL.md) | starting a daily coaching session — turns MCP context into today's training decision + nutrition guidance |
| [`t4l-write-results`](t4l-write-results/SKILL.md) | about to write any app result via MCP — gives payload shapes + a validator so the app won't discard the result |
| [`t4l-answer-chat`](t4l-answer-chat/SKILL.md) | the athlete has sent in-app chat messages — drains pending chat via MCP and posts short, workout-aware replies |

The one-time server/MCP bootstrap (`docs/initial_setup.md`) is intentionally
**not** a skill — it's environment setup, not a model capability.

## Design constraints (for cross-harness portability)

Kept to the lowest common denominator so one `SKILL.md` runs everywhere:

- **Frontmatter is `name` + `description` only.** No vendor-specific fields
  (`model`, `mode`, `hooks`, `allowed-tools`) — other harnesses ignore or reject
  them.
- **Descriptions ≤200 chars** (the strictest cap, claude.ai) and start with an
  explicit "Use when…" trigger, because activation is the model's judgment, not
  deterministic matching — weaker / open-weight models need the help.
- **Small catalog (4 skills).** Trigger reliability degrades as the catalog
  grows.
- **Bundled scripts are optional.** `t4l-write-results` ships a dependency-free
  Python validator (`scripts/validate_payload.py`); a harness without code
  execution can hand-check against the documented rules instead.

## Deploying to a harness

**The agent self-installs these during setup.** `docs/initial_setup.md`
instructs the coaching agent to copy/symlink the `skills/` folders into its own
harness skills directory, so a non-technical user never runs git or copies files
— they just launch the agent. Skills are scanned at startup, so a fresh install
takes effect from the next session. The manual commands below are for devs or
for pre-seeding a machine.

Discovery paths differ per harness, so point each one at these skills with a
copy or symlink, e.g.:

```bash
# Claude Code (also works for harnesses that read .claude/skills or .agents/skills)
ln -s "$PWD/skills/t4l-onboard-athlete" ~/.claude/skills/t4l-onboard-athlete
ln -s "$PWD/skills/t4l-coach-daily"     ~/.claude/skills/t4l-coach-daily
ln -s "$PWD/skills/t4l-write-results"   ~/.claude/skills/t4l-write-results
ln -s "$PWD/skills/t4l-answer-chat"     ~/.claude/skills/t4l-answer-chat

# Or use the cross-harness installer (Gemini CLI, Codex, OpenCode, Cursor, …):
npx skills install <this-repo-url>
```

The bootstrap docs (`docs/`) remain the canonical source of truth — agents still
read `docs/setup_instruction.md` first to start the server and connect MCP. The
skills cover the coaching phase that follows.

## Validator quick reference

```bash
cd skills/t4l-write-results
python scripts/validate_payload.py training_block_plan path/to/block.json
cat plan.json | python scripts/validate_payload.py next_day_plan
python scripts/validate_payload.py next_day_plan plan.json \
  --recent-context planning-context.json
```

`ERROR:` = the app would discard it (exit 1). `WARN:` = contract field missing
or coaching-quality concern that needs review but is not fatal (exit 0).
