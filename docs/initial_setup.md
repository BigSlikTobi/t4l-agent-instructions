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

## Install Coaching Skills (one-time, self-service)

If your harness supports Agent Skills (the `SKILL.md` convention), install the
T4L coaching skills into your own skills directory so future sessions load them
automatically. **Do this for the user — they do not run git or copy files by
hand.**

1. Locate your harness's skills directory. Common locations:
   - Hermes: `~/.hermes/skills/`
   - OpenClaw: `~/.openclaw/workspace/skills/`
   - Claude Code: `.claude/skills/` (project) or `~/.claude/skills/` (global)
   - Gemini CLI / OpenCode: their skills dir (e.g. `.agents/skills/`,
     `.opencode/skills/`, or `~/.gemini/...`).

   If unsure, check your harness docs for "skills directory".
2. For each skill folder in this repo's `skills/` directory —
   `t4l-onboard-athlete`, `t4l-coach-daily`, `t4l-write-results`,
   `t4l-answer-chat` — make it available there. Prefer a symlink so `git pull`
   keeps it current; copy the
   folder if symlinks are unsupported. If you only have remote access to this
   repo, fetch each skill's `SKILL.md` (plus `t4l-write-results/reference/` and
   `scripts/`) and write them into the skills directory.
3. Make it idempotent: if a T4L skill is already present, refresh it rather than
   creating a duplicate.
4. Skills are scanned at harness **startup**, so a freshly installed skill takes
   effect from your **next** session. Reload or restart the harness if it
   supports that. For this first session, keep following these docs directly —
   they are the source the skills were built from.

If your harness does not support skills, skip this section. The `docs/` workflow
works exactly as before.

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

For daily planning, the source of truth also supplies the comparison window.
Use recent logs, the accepted block, the prior next-day plan, coaching notes,
and recent chat to check whether today's session or wording is a stale repeat.
Do not decide that a plan is fresh from the current-day context alone.

Missing files, missing metrics, missing HealthKit permissions, or absent logs
are unknown, not zero. If `day_context` is missing or stale, ask the user to
open the app and push fresh context before coaching.

## Finish Setup: Restart the Gateway and Verify

Skills are scanned at startup, so finish setup with a **full gateway restart** to
load any freshly installed skills and confirm the whole stack comes back up.

**Restart only when something changed this setup** — a skill was just installed
or updated, or the server/MCP was just started. If the T4L skills already appear
in your catalog and the server and MCP are already up, setup is complete; **do
not restart again.** A restart makes you re-read these docs, so an unconditional
restart would loop.

When a restart is warranted:

1. Perform a full gateway/harness restart — a real process restart so skills are
   re-scanned, not just a new chat.
2. The restart ends this session; continue in the fresh one.
3. Verify before coaching:
   - the T4L server is still running and reachable at the printed URL,
   - MCP reconnects and `get_day_context` returns,
   - the skills `t4l-onboard-athlete`, `t4l-coach-daily`, `t4l-write-results`,
     and `t4l-answer-chat` appear in your catalog.

   If a skill is missing, re-run "Install Coaching Skills", restart once more,
   then proceed.

If your harness has no separate gateway, restarting the harness/CLI achieves the
same re-scan. If it cannot restart itself, ask the user to restart it once, then
continue.
