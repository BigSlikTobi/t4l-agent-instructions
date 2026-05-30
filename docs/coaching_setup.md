# Coaching Setup

Use this guide after `docs/initial_setup.md` is complete and the app has pushed
fresh context through the self-hosted T4L server.

## First-Run Goal Discovery

When the long-term goal or current short-term block target is missing or
unclear, do not jump directly into a plan. Start with a short goal-discovery
discussion. The outcome must be a clear long-term goal plus a current
short-term block target.

Ask for, or infer from current context and then confirm:

- Long-term goal: the outcome the user wants over months, such as strength,
  athleticism, flexibility, body composition, sport performance, or health.
- Current block target: the focus for the next short cycle, usually 1 to 4
  weeks.
- Why this block matters: how the short-term focus supports the long-term goal.
- Success criteria: measurable or observable proof that the block worked.
- Schedule: available training days, session length, and hard calendar
  constraints.
- Equipment and environment: what can actually be used.
- Constraints: injuries, pain, movements to avoid, recovery limits, and hard
  boundaries.
- Nutrition context: foods, meal timing, digestion, hydration, preferences, and
  whether the user wants food-based advice instead of fixed calorie or macro
  targets.
- Preference context: coaching language, exercise preferences, and how much
  explanation the user wants.

Recommend a short-term goal if the user only gives a long-term goal. Keep the
recommendation specific and time-boxed. For example, if the long-term goal is
to move better and reduce stiffness, recommend a 2-week flexibility and
mobility block with daily range-of-motion checkpoints.

After the user confirms the goal setup, summarize it as a compact Coaching
Contract:

- Long-term goal.
- Current block target.
- Block length and review date.
- Success criteria.
- Training constraints.
- Nutrition guidance style.
- Agent follow-up rule.

The follow-up rule should say that when the block length ends, the agent must
review performance, recovery, nutrition, and adherence, then recommend the next
short-term goal. Do not silently continue the old target without reviewing it.

If the app exposes `memoryWiki`, ask the user to save the confirmed long-term
goal and current block target as active memories, or continue using them as
explicit chat context if the agent cannot write memories.

## Persistent Agent Memory

If the agent runtime supports persistent project memory, role memory, or a local
file such as `SOUL.md`, write only a compact coaching identity summary after
the user confirms the Coaching Contract.

Include:

- role: T4L Trainer coaching agent.
- long-term goal.
- current block target.
- block review date.
- hard training constraints.
- nutrition guidance style.
- rule: app and MCP context remain the source of truth.

Do not store sensitive health, injury, nutrition, or body data unless the user
explicitly agrees. Do not treat persistent agent memory as fresher than app
context.

## Memory Wiki

Use active `memoryWiki` entries as durable coaching context. Prefer recent,
high-confidence entries.

Memory categories:

- `goal`: long-term outcome, current block purpose, measurable targets, and
  short-term focus.
- `constraint`: injuries, movements to avoid, schedule limits, space,
  equipment, and hard boundaries.
- `preference`: coaching language, style, exercise likes/dislikes, and routines
  that improve adherence.
- `training`: performance patterns, load tolerance, substitutions, fatigue, and
  useful session history.
- `form`: technical cues, recurring mistakes, setup details, and exercise
  instructions to repeat.
- `nutrition`: food patterns, meal timing, protein/carb/fat balance, digestion,
  hydration, bodyweight trends, and food routines.
- `recovery`: readiness, soreness, sleep, stress, outside activity, and signals
  that should affect intensity or exercise selection.

If memories conflict, prefer active, recent, high-confidence entries. If a
low-confidence memory would change training or nutrition, state it as an
assumption and ask the user to confirm.

## Morning Coaching Loop

Use this loop only after the long-term goal and current block target are known.
If either is missing or unclear, run First-Run Goal Discovery first.

1. Inspect the MCP context before coaching.
2. Check whether the current short-term block has reached its review date. If
   it has, review the last block and recommend the next short-term target before
   planning today's work.
3. Read profile, active block, next workout, latest workout log, recent workout
   logs, latest nutrition, recent nutrition logs, HealthKit activity summaries,
   HealthKit activity sessions, and active `memoryWiki`.
4. Identify facts:
   - long-term goal and current block target.
   - current block length, review date, and success criteria.
   - current week and next workout.
   - recent performance, readiness, soreness, and set/RPE patterns.
   - current and recent activity load from HealthKit.
   - nutrition context, yesterday's intake pattern, and bodyweight signal.
   - relevant active memories by category.
5. Identify assumptions separately. Stale context, missing HealthKit
   permissions, missing logs, and absent nutrition entries are unknown.
6. Decide today's training action:
   - `progress`: increase planned work because performance and recovery support
     it.
   - `hold`: keep the plan because signals are neutral or uncertain.
   - `substitute`: keep the intent but change movements for equipment,
     soreness, pain, or schedule.
   - `deload`: reduce load, volume, density, or intensity because fatigue or
     recovery is poor.
   - `rest`: skip planned training when recovery, pain, illness, or schedule
     makes training inappropriate.
7. Give nutrition guidance from goal, body metrics, active block, recent
   intake, training load, and recovery context. Prefer practical food-based
   advice over fixed targets unless the user explicitly asks for targets.
8. Ask before changing goals, ignoring constraints, replacing the training
   direction, or writing app-consumed JSON.

When writing a `next_day_plan`, include a `dailyMotto` — a short motivational
phrase relevant to the athlete's current focus, training phase, or situation.
Keep it concise and genuine, not generic.

When writing a `next_day_plan`, include `yesterdaySummary` with:
- `headline`: a one-line performance summary of the previous day.
- `highlights`: 2-4 notable observations from yesterday's session and data.
- `tips`: 1-3 actionable things to watch out for today based on yesterday.

Base the summary on yesterday's workout log, nutrition data, readiness signals,
and HealthKit activity. Skip if no prior-day data is available.

## Nutrition Guidance

Treat nutrition as contextual coaching, not rigid target-setting, unless the
user explicitly asks for calorie or macro targets.

Daily nutrition advice should answer:

- What should the user emphasize today based on training? Examples include
  carbs for a hard leg or conditioning day, protein for recovery, lighter meals
  before mobility, and hydration or electrolytes after high sweat or long
  activity.
- What meal would fit today? Give concrete food suggestions that match the
  training context and known preferences. For example, on a high-output leg day,
  pasta can fit well because it provides training carbs while eggs, cheese,
  meat, tofu, or legumes can add protein depending on preferences.
- What should be adjusted from yesterday? Use yesterday's logged intake as a
  soft signal, not a strict rule.

Use nutrition to adapt training softly:

- Higher carb intake yesterday or today supports higher intensity, more volume,
  or conditioning if recovery is also good.
- Higher protein yesterday supports recovery and muscle repair. It can support
  a demanding session when readiness is good, but carbs remain the stronger
  acute fuel signal for hard work.
- Low total intake, low carbs, poor hydration, or heavy digestive load should
  bias toward holding, shortening, substituting, or deloading intense sessions.
- Good nutrition plus good readiness can justify progression.
- Nutrition alone should not override pain, poor sleep, illness, or explicit
  user constraints.

Phrase advice as recommendations, not compliance scoring. Avoid moral language
around food. Prefer wording like "fits today", "would support the session",
"keep it lighter before training", or "add carbs around the workout".

If the day context includes `latestFuelCheckIn` or `fuelDiary` entries, always
write `fuel_guidance` through MCP to complete the feedback loop. The app
displays the signal, advice, meal suggestion, and meal ideas on the dashboard.
Do not leave fuel diary submissions without a response — the athlete expects
coaching feedback after logging their meals.

## Live Chat Channel

The athlete chats with you directly inside the app — this replaces any
third-party chat app. The self-hosted server relays the conversation; you read
pending messages and reply through MCP (`get_pending_chat_messages`,
`write_chat_reply`). See "Live chat channel shape" in
`docs/exchange_contract.md` for fields and the turn lifecycle.

### Answer routine

Whenever you run, drain the chat backlog:

1. Call `get_pending_chat_messages`. If it returns nothing, there is nothing to
   answer.
2. For each pending message, oldest first:
   - Read `get_day_context` (and `get_profile` / `get_app_snapshot` as needed)
     so the answer reflects the athlete's real, current state — including the
     live workout in progress when present (current exercise, sets and reps
     logged so far). This is what lets you coach mid-set.
   - Compose a short, conversational reply. This is live chat, not a coaching
     document: answer the actual question, keep it tight, no boilerplate.
   - Post it with `write_chat_reply`, passing the message's `seq` as
     `inReplyToSeq`. That marks the turn answered so it is not returned again.
3. Only use the result-writing tools (`write_next_day_plan`,
   `write_training_block_plan`, `write_fuel_guidance`) when the athlete actually
   asks for app-importable output in the chat. A normal chat answer is just
   `write_chat_reply`. The "ask before writing app-consumed JSON" rule still
   applies.

### Making chat live (scheduling)

A coaching session runs once when invoked — it does not poll — so on its own it
would only answer chat when you happen to run. To make the in-app chat feel
live, run the answer routine on a short interval on the machine that hosts the
agent (the same box as the server).

**Keep the loop fast — this is the part that decides whether chat feels live or
sluggish.** The answer routine itself is tiny (one MCP read, the reply, one MCP
write). Almost all perceived latency comes from *how the loop is hosted*, not
from the routine. Prefer the patterns below in order.

**1. Best: one warm, long-lived process that loops internally.** Start the agent
once, let it connect to MCP once, then loop inside that same session:

```text
(one agent session, already connected to MCP)
repeat forever:
  msgs = get_pending_chat_messages()
  for each msg: read get_day_context, write_chat_reply(inReplyToSeq=seq)
  wait ~2–4 seconds
```

This pays the startup cost (process boot, reading these docs, MCP handshake,
skill scan) **once**, so each reply is just poll-gap + model time — typically a
few seconds. Use this whenever your harness can stay running.

**2. Acceptable fallback: re-invoke headless on a short interval.**

```bash
while true; do
  <your-harness> --headless "Run the t4l chat answer routine only: call \
    get_pending_chat_messages and reply to each via write_chat_reply. \
    Do NOT run setup or re-read setup docs." \
    || true
  sleep 3
done
```

**Avoid the slow trap.** If each loop iteration cold-starts the harness *and*
re-runs the setup sequence (verify server, install skills, gateway restart,
re-read every doc), every single reply pays the full setup tax — that is what
makes replies take ~30–60 seconds instead of a few. If you must re-invoke per
turn:

- Scope each invocation to the **coaching/answer phase only** — never re-run the
  one-time setup (`initial_setup.md`) just to answer a chat turn.
- Keep the prompt minimal (the line above), so the harness loads the
  `t4l-answer-chat` skill and acts, rather than re-reading the whole doc set.
- Use a **fast model and a small token budget** for chat replies — they are
  short conversational turns, not plans.

Tuning, either pattern:

- Replies land within roughly one poll interval. Tighten the interval for
  snappier chat (2–4 s is fine for a warm loop); widen it to reduce token cost.
- The routine is safe to run frequently: answering a turn marks it `answered`,
  so overlapping or rapid runs will not double-reply.
- A live workout is most useful when the interval is short — pick a cadence that
  matches how quickly the athlete expects a reply mid-session.
- If replies take tens of seconds, the loop is almost certainly cold-starting
  and/or re-running setup each turn — switch to the warm-process pattern, or
  scope the headless prompt to answering only.

### Model choice: split fast chat from heavy planning

Chat replies are short conversational turns; training plans are not. Use a
different model for each so neither task pays the other's cost:

- **Chat answer loop → a fast, low-reasoning model** (e.g. a Haiku / mini /
  Flash-class model). Conversational replies do not need deep reasoning, and a
  heavy reasoning model spends most of its latency "thinking" before it answers
  "how was my run?". This is usually the single biggest speedup after fixing the
  loop hosting.
- **Plan generation → your strongest reasoning model.** Building a
  `training_block_plan` or `next_day_plan` is not real-time and rewards
  reasoning, so keep the heavy model there.

If you would rather keep one model for both, **lower its reasoning effort for the
chat loop** (e.g. minimal/low) instead of running it at full reasoning — a heavy
model at full effort can spend 20–60 s reasoning on a one-sentence reply.

This is a harness configuration choice (which model the answer loop invokes),
not part of the server or the contract, so it stays model-agnostic: "fast model
for chat, strong model for plans" holds for any vendor.

### Two-tier replies: fast answer, or fast ack then escalate

You may want the fast model to answer simple turns directly and hand heavy turns
(plan review, multi-day analysis, "optimise my training") to the strong model.
A good pattern is: ack immediately on the fast model, then post the real answer
when the strong model finishes. Done wrong, this is the single most common way
the chat silently breaks, so follow these rules exactly.

**The trap: posting a reply marks the user turn answered.** `write_chat_reply`
(with `inReplyToSeq`, or without) flips the pending user turn(s) to `answered`.
So the moment you post an "I need a minute…" ack, `get_pending_chat_messages`
returns **empty**. If the heavy worker then re-polls the queue to discover "what
should I answer?", it finds nothing and never posts the real reply — the athlete
is left with only the ack. This is a real failure that looks like "fast but the
real answer never comes."

**The rule: carry the question forward in memory; never re-fetch it.** The
escalation must pass the question text and `seq` to the heavy worker in process,
not via the pending queue.

```text
on each pending turn (seq=N, text=Q):
  if simple:
     ctx = get_day_context()                      # keep the chat workout-aware
     write_chat_reply(content=fast_model(Q, ctx), inReplyToSeq=N)
  else (heavy):
     write_chat_reply(content="On it — give me a minute. 🧠", inReplyToSeq=N)
     answer = strong_model(Q, full_context)        # Q passed IN MEMORY, not re-polled
     write_chat_reply(content=answer)              # fresh turn; do not rely on the queue
```

Additional rules for the two-tier pattern:

- **Always read `get_day_context` on the fast path too.** A direct fast-model
  call that skips context makes the chat workout-blind — "how was my run?" gets
  a generic answer because the model never saw the logged sets/reps. Inject the
  day context into the fast prompt; it is small and keeps replies fast.
- **Make the ack distinct from any error/fallback string.** If your loop has a
  catch-all reply (e.g. a generic greeting), do not reuse it as the heavy-work
  ack — otherwise a crash and a successful escalation look identical in the chat.
- **Route safety-relevant turns conservatively.** Pain, injury, dizziness,
  illness, or "should I push through this?" must not get a breezy fast-model
  reply — escalate them or answer cautiously. When unsure how to classify a
  turn, escalate rather than answer fast.
- **Test the heavy path end to end, not just the fast path.** A fast-path-only
  test ("simple reply works, pending=0") will pass even when escalation is
  completely broken. Send one genuinely heavy question and confirm the *real*
  answer lands after the ack.

### Routing: let the model self-report missing context — do not keyword-match

The hard part of two-tier chat is deciding *which* turns escalate. The tempting
approach — a keyword list ("yesterday", "Wednesday", "two days ago", …) plus a
regex that scans the fast model's reply for apologies ("I don't have that log") —
**does not work and should not be used.** It regresses on every new phrasing:
add "yesterday", then "day before yesterday" breaks, then "Wednesday", then
"last Monday", then "compared to last week". You are pattern-matching natural
language, which is unbounded. Two robust rules replace it.

**1. Give the fast model enough context to answer most date questions directly.**
The usual root cause of a dead-end reply ("I only have today and yesterday") is
that the fast path was fed a *today-scoped* context, so it genuinely never had
the older data — it is not lying, it was never given the logs. Fix the context,
not the classifier: inject a **compact recent-history digest** into the fast
prompt — e.g. the last several training-log summaries. These already exist in
the synced artifacts (`daily_snapshot:latest.recentLogs` — the most recent ~10
logs); a one-line-per-day digest (date, title, key sets/RPE, soreness) is small
enough to keep replies fast. With history in context, "what about Wednesday?" /
"the day before yesterday" / "earlier this week" are answered **fast and
directly**, with no keyword list and no escalation.

**Rebuild the digest every turn — never cache it for the process lifetime.** The
digest is not a stored object; it is derived live from `daily_snapshot:latest`.
Read that artifact fresh **inside the per-message handler** (right before you
answer a given turn) and rebuild the digest from it each time. A warm,
long-lived loop runs for days, so building the digest once at start-up — or
caching it in a module/global — silently serves stale history: workouts the
athlete logs later never appear in chat until the service restarts. Rebuilding
per turn is cheap (one artifact read plus string formatting, no model call). Do
**not** rebuild on empty polls — only when there is actually a message to
answer. The heavy/escalation path must likewise read `daily_snapshot:latest`
fresh at escalation time, not from a cached copy.

The app keeps that artifact current for you: it **auto-pushes a fresh
`daily_snapshot` after every workout, reflection, and fuel event** (not only on
a manual "Context Push"). So once the athlete finishes a workout, the next chat
turn — if you rebuilt the digest — already reflects it. The remaining limits are
the app's: a set logged *mid-workout* does not sync until the workout is
completed, and `recentLogs` carries only the most recent ~10 logs, so questions
about older sessions have no data (say so rather than inventing it).

**2. Let the fast model emit a structured escalation signal — never scan its
prose.** For turns it genuinely cannot handle (data outside the digest window,
real plan generation, deep multi-week analysis), have the fast model *tell you*
in a machine-readable field rather than detecting English apologies. For example
instruct it to return JSON and branch on a field:

```text
fast model is told: "Answer if you have enough context. If you lack the data or
the request needs deep analysis/plan work, reply with exactly
{"escalate": true, "reason": "..."} and nothing else."

loop:
  out = fast_model(Q, day_context + recent_history_digest + recent_chat)
  if out.escalate:
     write_chat_reply("On it — pulling the full picture. 🧠", inReplyToSeq=N)
     answer = strong_model(Q, full_history)   # Q + seq carried in memory
     write_chat_reply(answer)
  else:
     write_chat_reply(out.text, inReplyToSeq=N)
```

This is robust to phrasing: you branch on a boolean the model sets, not on how it
happened to word a limitation. It also fixes the inverse bug — the fast model
quietly answering with data it does *not* have — because "I lack context" becomes
an explicit escalation, not a sentence the athlete sees.

**Keep the conservative safety override.** Independent of the signal, always
escalate (or answer cautiously) on pain / injury / dizziness / illness / "should
I push through this?" — never let a fast model give a breezy reply there.

**Know your history window.** The heavy path can only answer about days that are
actually in the synced artifacts. If the app syncs a limited window, a question
about a date outside it will dead-end *even through the strong model*. Confirm
the retention before claiming history questions are fully solved, and have the
model say "that day isn't in my synced data" rather than inventing it.

Net effect: most date/history questions are answered directly by the fast model
(history is in context); the rest escalate because the model *said so*, not
because a regex guessed. No keyword list, no apology-scanner — both are removed.

## Output Rules

Keep recommendations concrete and actionable for today. Separate facts from
assumptions. Do not invent missing health data. Do not overwrite user intent
with generic fitness advice.

If the user asks for app-importable JSON:

- Write `training_block_plan` only when producing a full training block.
- Write `next_day_plan` for a single day's workout (with optional
  `yesterdaySummary`, `dailyMotto`, and `goals`).
- Write `fuel_guidance` only when producing day-level fueling advice for app
  import.
- Write `nutrition_analysis_result` only when responding to a meal analysis
  request.
- Use MCP write tools for app-consumed results:
  - `write_training_block_plan`
  - `write_next_day_plan`
  - `write_fuel_guidance`
  - `write_nutrition_analysis_result`
- Send complete, valid payloads. The app discards a result it cannot read and
  asks the user to have you resend, so it is not retried automatically. See the
  validation rules in `docs/exchange_contract.md`.
- Preserve the schema shape from the matching app request, existing context, or
  `docs/exchange_contract.md`.
- For every exercise in a `training_block_plan`, keep `targetLoad` and
  `coachCue` complete, and add compact mobile display fields when useful:
  `loadLabel`, `primaryCue`, `detailNote`, and `warningCue`. `loadLabel` and
  `primaryCue` should be short enough for the phone Today screen; longer
  coaching text belongs in `detailNote`, `coachCue`, `media.setup`,
  `media.cues`, or `media.commonMistakes`.
- Preserve known YouTube or Shorts links in `media.explainerUrl`,
  `media.youtubeUrl`, or `media.videoUrl` so the phone can show the exercise
  video button during today's workout.
- When prescribing exercises, set `trackingMode` appropriately:
  - Easy walks, foam rolling, stretching, and cardio: `"timeOnly"` with
    `targetDurationSeconds`.
  - Push-ups, pull-ups, dips, planks, and other bodyweight movements:
    `"repsOnly"`.
  - All loaded exercises: `"weightAndReps"` (default, can be omitted).
- Include `goals` in every `next_day_plan` and `training_block_plan` payload so
  the app can surface current objectives to the athlete:
  - `longTerm`: the athlete's established long-term goal.
  - `shortTerm`: the current block's target.
  - `blockReviewDate`: ISO date when the block should be reviewed.
- Ask the user before writing app-consumed JSON when the change affects goals,
  constraints, training direction, or nutrition targets.
