# Journal

Read this file after the setup sequence. It documents contract changes and new
capabilities so you can use them immediately.

---

## 2026-05-30 — Chat freshness: snapshot auto-pushes; rebuild the digest per turn

Two changes that keep the in-app coach chat current.

**The app now auto-pushes `daily_snapshot` on workout events.** Previously the
daily snapshot (which carries `recentLogs`, your recent-training history) was
sent only when the athlete tapped "Context Push". Now the app refreshes it after
**every workout completion, reflection, and fuel event**, alongside the existing
`day_context` push. So the athlete's recent history reaches the server
automatically — no manual push needed for the chat to know about a workout they
just finished.

**You must rebuild the recent-history digest every turn — never cache it.** The
digest is derived live from `daily_snapshot:latest`; read it fresh inside the
per-message handler each time you answer. A warm chat loop runs for days, so
building the digest once at start-up serves stale history. Rebuilding per turn
is cheap (one artifact read, no model call); don't rebuild on empty polls.

Limits to respect (say so, don't invent): a set logged *mid-workout* is not on
the server until the workout completes, and `recentLogs` holds only the ~10 most
recent logs, so older sessions have no data.

See "Routing" in `coaching_setup.md` and the updated `freshness_rules.md`.

---

## 2026-05-29 — Live in-app chat channel (replaces 3rd-party chat apps)

The athlete now chats with you **inside the T4L app**, not through Slack,
Telegram, or any other chat app. The self-hosted server relays the conversation;
you read pending messages and post replies over MCP. The app is just the chat
surface — your model, skills, and context stay where they run today.

### Two new MCP tools

- `get_pending_chat_messages` — list unanswered athlete messages, oldest first.
- `write_chat_reply` — post a reply; arguments `content` (non-empty string) and
  optional `inReplyToSeq` (the `seq` of the message you are answering). Posting
  marks the answered turn(s) so they are not returned again.

Message fields and the turn lifecycle are documented under "Live chat channel
shape" in `exchange_contract.md`. Delivery is message-level (one complete reply
per turn — no token streaming yet). The new `t4l-answer-chat` skill covers the
answer routine for skills-capable harnesses.

### Answer routine

On each run: call `get_pending_chat_messages`; for each pending message, read
`get_day_context` (so the reply reflects the live workout in progress — current
exercise, sets/reps logged), write a short conversational reply, and post it
with `write_chat_reply(inReplyToSeq=<seq>)`. A chat answer is just
`write_chat_reply` — only use the `write_*` result tools when the athlete
actually asks for app-importable output.

### Making it live (important)

A coaching session runs once when invoked and does **not** poll, so on its own
it only answers chat when you happen to run. To make chat feel live, run the
answer routine on a short interval on the agent's host — a watch loop or `cron`
that invokes your harness headless every ~20–30 s with "answer the chat
channel." Tighten the interval for snappier replies, widen it to cut token cost.
The routine is safe to run often: answered turns are not returned again, so runs
never double-reply. See "Making chat live (scheduling)" in `coaching_setup.md`.

### What to do differently starting now

1. Drain the chat backlog whenever you run — do not leave pending messages
   unanswered.
2. Schedule the answer routine so the in-app chat is actually live (see above).
   Without scheduling, the channel only works when you are already running.
3. Keep chat replies short and conversational; reach for `write_*` result tools
   only when the athlete asks for app-importable output.

---

## 2026-05-29 — Agent Skills: portable SKILL.md coaching skills + payload validator

The repo now ships **Agent Skills** under `skills/` — the on-demand procedural
layer for the coaching phase. They follow the open `SKILL.md` convention
(agentskills.io), so any skills-capable harness (Claude Code, Codex CLI, Gemini
CLI, OpenCode, OpenClaw, Hermes, …) on any sufficiently capable model can load
them. The harness handles discovery and progressive disclosure; you act on a
skill's body when its description matches the task.

### The three skills

- `t4l-onboard-athlete` — first-run goal discovery and the Coaching Contract,
  when the long-term goal or current block target is missing or unclear.
- `t4l-coach-daily` — the morning coaching loop: turn synced MCP context into
  today's action (`progress` / `hold` / `substitute` / `deload` / `rest`) plus
  nutrition guidance and the fuel round-trip.
- `t4l-write-results` — which MCP write tool to use, the full payload shapes
  (`reference/payload-shapes.md`), and a validator (below).

The skills distil `coaching_setup.md` and `exchange_contract.md`; those docs
remain the canonical reference. The one-time server/MCP bootstrap
(`initial_setup.md`) is intentionally **not** a skill.

### Validate result payloads before writing them

`skills/t4l-write-results/scripts/validate_payload.py` reproduces the app's
import rules so you can self-check a payload before calling a write tool — the
app discards an unreadable result once, with no retry.

```bash
python skills/t4l-write-results/scripts/validate_payload.py <kind> payload.json
# or:  cat payload.json | python .../validate_payload.py <kind>
# kind = training_block_plan | next_day_plan | fuel_guidance | nutrition_analysis_result
```

`ERROR:` lines (exit 1) are what the app would discard; `WARN:` lines (exit 0)
are non-fatal contract gaps. It is dependency-free (standard library only).

### What to do differently starting now

1. If your harness supports skills, self-install them during setup — see
   "Install Coaching Skills" in `initial_setup.md`. The agent installs the
   `skills/` folders into its own skills directory so future sessions load them
   automatically; the user never copies files by hand. Finish setup with a full
   gateway restart **when something changed** (skills are scanned at startup, so
   the restart loads them) — but skip the restart when everything is already
   loaded and running, or you will loop. If your harness does not support skills,
   the `docs/` still work exactly as before.
2. Before any MCP write, run `validate_payload.py` on the payload (or hand-check
   against `t4l-write-results/SKILL.md`) and fix every `ERROR`.
3. Keep reading `docs/setup_instruction.md` first — skills cover coaching, not
   the server/MCP bootstrap.

---

## 2026-05-28 — Server 0.2.0: write validation, no silent retries, complete tool list

The self-hosted server is now `t4l-server` 0.2.0. Install and run are unchanged
(`pipx install t4l-server`, then `t4l-server serve --data-dir ~/T4LServerData`).
Add `--log-level DEBUG` when troubleshooting a connection.

### Results are validated and bad ones are dropped, not retried

This is the most important change. The app validates each result when it imports
it. A result it cannot read is **discarded once** and the user is told to ask you
to resend — there is no silent retry loop anymore. Send complete, valid payloads
the first time. The app rejects:

- `training_block_plan`: empty `workouts`, or `durationWeeks` below 1.
- `next_day_plan`: a workout with no `exercises`.
- `nutrition_analysis_result`: `calories` not greater than 0, or a negative macro.

`fuel_guidance` is always accepted. If you learn a result was discarded, fix the
payload and write it again.

### Always set a valid `schema`

The server now rejects a write whose `schema` field is present but not a
non-empty string. Set the correct `schema` on each result (e.g.
`"fuel_guidance.v1"`, `"nutrition_analysis_result.v1"`), or omit it to accept the
default `<kind>.v1`.

### Complete tool inventory (see `exchange_contract.md`)

- `write_next_day_plan` is a first-class write tool — earlier tool lists omitted
  it. Use it for single-day workouts.
- Read tools are now documented in full, including `get_training_block_request`,
  `get_nutrition_analysis_request`, and `get_blob_base64` (read a meal photo by
  the `name` from the request).
- The `nutrition_analysis_result` payload shape is now documented. Echo the
  request's `requestId` and keep `calories` above 0.

### `t4l-bridge` command removed

Older setups exposed a `t4l-bridge` alias. It is gone — start the server with
`t4l-server` only.

### What to do differently starting now

1. Send complete, valid result payloads — there is no retry safety net anymore.
2. Set a correct `schema` string on every result (or omit it for the default).
3. Use `write_next_day_plan` for single-day plans, and the documented
   `nutrition_analysis_result` shape for meal analyses.
4. Run the server with `t4l-server` (never `t4l-bridge`).

---

## 2026-05-27 — Contract v2: Tracking Modes, Daily Coaching Context, Fuel Round-Trip

### Exercise tracking modes

Exercises now carry an optional `trackingMode` field. Set it when prescribing:

- `"weightAndReps"` (default, can be omitted) — weighted exercises.
- `"repsOnly"` — bodyweight exercises (push-ups, pull-ups, dips, planks).
  The app hides the weight input.
- `"timeOnly"` — cardio, stretching, easy walks, foam rolling. The app shows
  a duration stepper instead of weight/reps. Include `targetDurationSeconds`
  (integer) and set `reps` to a human-readable label like `"20 min"`.

Old agents that omit `trackingMode` still work — the app defaults to
`weightAndReps`.

### Daily coaching context in next-day plans

`write_next_day_plan` now accepts optional coaching metadata alongside the
workout object:

- `dailyMotto` (string) — short motivational phrase. The app shows it inside
  the Today hero card as an italic quote.
- `yesterdaySummary` (object) — previous-day performance review:
  - `headline`: one-line summary.
  - `highlights`: 2-4 bullet observations.
  - `tips`: 1-3 actionable watch-outs for today.
  The app displays this in the Coach > Plan tab.
- `goals` (object) — current coaching goals:
  - `longTerm`: the athlete's overarching goal.
  - `shortTerm`: the current block target.
  - `blockReviewDate`: ISO date when the block should be reviewed.
  The app displays this at the top of the Coach > Plan tab with a countdown
  badge. Include `goals` in both `write_next_day_plan` and
  `write_training_block_plan` payloads.

All fields are optional. The app hides the corresponding UI when they are
absent, so old agents are unaffected.

### Fuel guidance round-trip

The fuel feedback loop is now fully wired:

1. The athlete logs meals in the Fuel Diary and submits with a quality score.
2. The app pushes `latestFuelCheckIn` and `fuelDiary` entries via day context.
3. **You must respond** by writing `fuel_guidance` through MCP whenever the day
   context contains fuel diary data. The app polls for it shortly after
   submission — do not leave diary entries without a response.

The `fuel_guidance` schema is documented in `exchange_contract.md`. Key fields:
`signal` (`green`/`hold`/`fuel`/`deload`), `todayAdvice`, `mealSuggestion`,
`yesterdayRead`, `mealIdeas`.

### What to do differently starting now

1. Set `trackingMode` on every exercise. Default is fine for loaded work —
   explicitly set `"repsOnly"` or `"timeOnly"` when appropriate.
2. Include `dailyMotto`, `yesterdaySummary`, and `goals` in every
   `write_next_day_plan` call.
3. Include `goals` in every `write_training_block_plan` call.
4. Always write `fuel_guidance` when the day context has fuel diary entries.
