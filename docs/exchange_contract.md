# Exchange Contract

The app and agent communicate through the self-hosted T4L server. The app uses
semantic REST endpoints. Agents use MCP tools. The server stores JSON payloads
in SQLite and does not own accepted training state.

## App uploads through REST

- `PUT /v1/app/snapshot`
- `PUT /v1/context/day`
- `PUT /v1/context/daily-snapshot`
- `PUT /v1/profile`
- `PUT /v1/requests/training-block`, `PUT /v1/requests/nutrition-analysis`
- `POST /v1/blobs/meal-images/{name}` for meal photos

There is no folder-based or `/files/{name}` exchange. The server rejects those
paths.

## Agent reads through MCP

- `get_day_context`: primary current-day context.
- `get_app_snapshot`: full phone sync payload when present.
- `get_profile`: athlete profile.
- `get_pending_requests`: pending app requests.
- `get_training_block_request`: latest pending training-block request.
- `get_nutrition_analysis_request`: latest pending meal-analysis request.
- `get_blob_base64`: read an uploaded meal image. Pass the name from the
  request, e.g. `{ "name": "meal_images/<file>.jpg" }`.
- `get_recent_chat_messages`: recent chat turns (answered and pending), oldest
  first, so the planner can see what the athlete actually said in chat. Optional
  `limit` (default 20, max 200). Distinct from `get_pending_chat_messages`, which
  returns only unanswered work.
- `get_coaching_notes`: the standing coaching notes you authored — explicit
  athlete requests and open questions extracted from chat that should shape
  planning. Returns the latest notes payload, or `null`.
- `get_planning_context`: the full planning working set in one call — day
  context, recent logs, profile, active block, next-day plan, fuel/nutrition,
  pending requests, coaching notes, and recent chat. Optional `recentChatLimit`
  (default 20, max 200). Prefer this for daily planning instead of stitching the
  reads above by hand.

## Agent results through MCP

- `write_training_block_plan`
- `write_next_day_plan`
- `write_fuel_guidance`
- `write_nutrition_analysis_result`

The app imports pending results only after user confirmation where needed;
training blocks always require explicit user import.

## Agent planning notes through MCP

- `write_coaching_notes`: persist the standing coaching notes (explicit athlete
  requests, open questions) so important chat intent survives after the bounded
  `recentChat` window rolls forward. Argument: `payload` (object). It
  **replaces** the latest notes, so read the current notes first with
  `get_coaching_notes`, merge, then write the whole set back. Unlike the result
  tools, these notes are not consumed by the app — they are context you write
  for your own future planning runs. See "Coaching notes shape" below.

## Live chat through MCP

The athlete chats with you directly inside the app — this replaces any
third-party chat app. The server relays the conversation; you read pending
messages and post replies through MCP.

- `get_pending_chat_messages`: list unanswered athlete messages. Returns
  `{ "messages": [ ... ] }`, oldest first.
- `write_chat_reply`: post a reply. Arguments: `content` (required, non-empty
  string) and `inReplyToSeq` (optional integer — the `seq` of the message you
  are answering). Returns `{ "posted": { ...the stored reply... } }`.

See "Live chat channel shape" below for message fields and the turn lifecycle.

## Delivery and validation

The server validates every write: a `schema` field, when present, must be a
non-empty string. Set the correct `schema` for each result, or omit it to accept
the default `<kind>.v1`. A non-string schema is rejected.

The app validates each result when it imports it. A result the app cannot read
is **discarded once** — it is not retried — and the user is told to ask you to
resend. There is no silent retry, so always send complete, valid payloads. The
app rejects:

- `training_block_plan`: empty `workouts`, or `durationWeeks` below 1.
- `next_day_plan`: a workout with neither non-empty `items` nor non-empty
  `exercises`.
- `nutrition_analysis_result`: `calories` not greater than 0, or a negative
  macro.

`fuel_guidance` is always accepted. If a result is rejected, fix the payload and
write it again.

## Coaching-quality preflight

Schema-valid is not the same as good coaching. Before writing a
`training_block_plan` or `next_day_plan`, compare the candidate with the fresh
`get_planning_context` bundle:

- `recentLogs`: recent exercise exposure, prescriptions, order, and completed
  training;
- `activeBlock`: the intent, anchors, and planned progression to retain;
- `nextDayPlan`: the prior generated session and recent app-facing copy;
- `coachingNotes` and `recentChat`: explicit constraints, requests, and variety
  preferences.

Keep block intent, primary anchors, progression, recovery, injury constraints,
equipment, schedule, and athlete preferences. On a normal training day, add at
least one meaningful fresh element when safe: a log-backed progression
challenge; one or two pattern-matched accessories; a format, sequence, tempo,
or density change; or a small goal-relevant skill/conditioning element. Do not
pair an unfamiliar element with a large increase in another stress lever.

Do not repeat the same exercise order and prescription from a recent
same-purpose session unless it is a deliberate benchmark, technique, rehab,
taper, or recovery repeat. Put a short explanation in the workout `rationale`:
what remains anchored, what is fresh, and why it fits today. If repetition is
deliberate, name the reason and metric being retested.

Compare app-facing wording too. Do not reuse a recent workout title,
`dailyMotto`, opening, summary, or fuel-advice sentence word for word. New words
alone do not make a stale session novel, and exact safety/form cues may repeat
when consistent wording protects the athlete. Rotate meal ideas only within
known food and digestion preferences; a preferred routine meal may stay when
its timing, portion, or reason is current. These are coaching-quality rules;
they do not add new required JSON fields.

## Training block plan shape

Use `write_training_block_plan` only for a complete block. Preserve the app's
existing JSON shape: a raw block object or `{ "block": { ... } }`.

Each block must include:

- `id`
- `style`
- `title`
- `durationWeeks`
- `currentWeek`
- `weeklyFocus`
- `measurableTargets`
- `workouts`
- `createdBy`
- `createdAt`

Valid `style` values are `rugby`, `boxer`, `hybrid`,
`strengthHypertrophy`, `conditioning`, and `custom`.

Each workout must include:

- `id`
- `week`
- `day`
- `title`
- `focus`
- `rationale`
- `conditioning`
- non-empty `items` for grouped/new plans, or non-empty `exercises` for simple
  flat plans

For workout structure:

- Use `exercises` only when the workout is a simple flat list.
- Use `items` when the workout contains supersets or circuits. `items` may
  contain flat exercise items and grouped items.
- A flat item has `type: "exercise"` plus the normal exercise prescription
  fields.
- A superset has `type: "superset"`, exactly 2 child exercises, and `rounds`.
  It executes A1, B1, A2, B2, etc. Do not write all sets of A before B.
- A circuit has `type: "circuit"`, 3 or more child exercises, and `rounds`.
  Use the JSON term `circuit`, never `circle`; German UI may display `Zirkel`.
- Do not nest groups inside groups in v1.
- In grouped items, `rounds` is the source of truth for repeated execution.
  Child `sets` may be `1`; the app displays/logs the child exercises against the
  group round count.
- `group.restSeconds` applies after the last child of each round. Child
  `restSeconds` applies between child steps and can be `0`.

Each exercise must include:

- `exerciseId`
- `name`
- `sets`
- `reps`
- `targetLoad`
- `targetRpe`
- `restSeconds`
- `coachCue`

For mobile execution, each exercise should also include these optional display
fields whenever useful:

- `loadLabel`: compact chip text for Today, for example `12-24 kg`
- `primaryCue`: one short row cue, ideally 3-8 words
- `detailNote`: longer coaching explanation for the detail sheet
- `warningCue`: short pain, range-of-motion, or safety cue
- `trackingMode` (optional, string): how the app should track this exercise.
  `"weightAndReps"` (default) tracks weight and reps per set.
  `"repsOnly"` tracks reps only — use for bodyweight exercises like push-ups,
  pull-ups, dips, and planks. `"timeOnly"` tracks duration only — use for easy
  walks, foam rolling, stretching, and cardio. If omitted, the app defaults to
  `"weightAndReps"`.
- `targetDurationSeconds` (optional, integer): prescribed duration for
  `"timeOnly"` exercises. The `reps` field should describe the activity in
  human-readable form (e.g. `"20 min"`).

Keep `targetLoad` and `coachCue` complete enough for logs, review, and future
agents. Use `loadLabel` and `primaryCue` to keep the phone workout screen
compact. If display fields are omitted, the app falls back to `targetLoad` and
`coachCue`, so long prose there will make the Today screen harder to scan.

Exercises should include `media` when setup, cue, mistake, or video context is
known. Preserve known YouTube or Shorts links; the phone uses them for the
Today exercise video button. `media` supports:

- `explainerUrl`, `youtubeUrl`, or `videoUrl`
- `setup`
- `cues`
- `commonMistakes`

Example exercise:

```json
{
  "exerciseId": "goblet_squat",
  "name": "Goblet Squat",
  "sets": 3,
  "reps": "8-10",
  "targetLoad": "Use the heaviest kettlebell that keeps tempo and depth clean.",
  "loadLabel": "16-24 kg",
  "targetRpe": 7.5,
  "restSeconds": 90,
  "coachCue": "Brace before every rep and keep pressure through the whole foot.",
  "primaryCue": "Brace before every rep",
  "detailNote": "Use a controlled eccentric. Stop adding load if depth changes.",
  "warningCue": "Stop if knee pain increases.",
  "media": {
    "setup": "Kettlebell tight to sternum, feet rooted.",
    "cues": ["Tripod foot", "Ribs down", "Drive evenly through both feet"],
    "commonMistakes": ["Losing heel pressure", "Knees collapsing inward"]
  }
}
```

Example grouped workout structure:

```json
{
  "id": "w1d2_density",
  "week": 1,
  "day": 2,
  "title": "Upper Density",
  "focus": "Superset push and pull patterns.",
  "rationale": "Alternating patterns keeps the session dense without rushing form.",
  "conditioning": "",
  "items": [
    {
      "type": "superset",
      "groupId": "ss_1",
      "title": "Superset 1",
      "rounds": 3,
      "restSeconds": 90,
      "exercises": [
        { "exerciseId": "push_up", "name": "Push-Up", "sets": 1, "reps": "10", "trackingMode": "repsOnly", "targetLoad": "bodyweight", "targetRpe": 7, "restSeconds": 0, "coachCue": "Brace and move as one line." },
        { "exerciseId": "row", "name": "Row", "sets": 1, "reps": "12", "targetLoad": "moderate", "targetRpe": 7, "restSeconds": 0, "coachCue": "Pull elbows back without shrugging." }
      ]
    }
  ]
}
```

```json
{
  "exerciseId": "easy_walk",
  "name": "Easy Walk",
  "sets": 1,
  "reps": "20 min",
  "trackingMode": "timeOnly",
  "targetDurationSeconds": 1200,
  "targetLoad": "Comfortable pace, nose breathing.",
  "targetRpe": 3,
  "restSeconds": 0,
  "coachCue": "Stay relaxed, use this as active recovery.",
  "primaryCue": "Nose breathing, easy pace"
}
```

```json
{
  "exerciseId": "push_up",
  "name": "Push-Up",
  "sets": 3,
  "reps": "12-15",
  "trackingMode": "repsOnly",
  "targetLoad": "Full range of motion, chest to floor.",
  "targetRpe": 7,
  "restSeconds": 60,
  "coachCue": "Keep core tight, elbows at 45 degrees.",
  "primaryCue": "Core tight, elbows 45°",
  "warningCue": "Stop if wrist pain increases."
}
```

## Next-day plan shape

Use `write_next_day_plan` for a single day's workout. The payload wraps a
workout object and optional coaching context.

```json
{
  "workout": { "...same shape as a block workout..." },
  "yesterdaySummary": {
    "headline": "Solid leg day — all sets hit at RPE 7-8",
    "highlights": [
      "Squat 3×8 at 80 kg felt strong",
      "Conditioning well tolerated"
    ],
    "tips": [
      "Shoulders may be fatigued — warm up extra today",
      "Keep RPE under 8 on pressing movements"
    ]
  },
  "dailyMotto": "Smooth reps build the next five kilos.",
  "goals": {
    "longTerm": "Build strength while staying athletic",
    "shortTerm": "Increase bench press 1RM by 5 kg",
    "blockReviewDate": "2026-06-15"
  }
}
```

All fields except `workout` are optional. If omitted, the app hides the
corresponding UI element.

- `workout` (required): the workout object (same shape as a block workout).
- `yesterdaySummary` (optional, object): previous-day performance summary.
  - `headline` (string): one-line performance summary.
  - `highlights` (array of strings): 2-4 notable observations.
  - `tips` (array of strings): 1-3 things to watch out for today.
- `dailyMotto` (optional, string): short motivational phrase for the day. Tie it
  to current context and do not reuse a recent motto word for word.
- `goals` (optional, object): current goal context.
  - `longTerm` (string): the athlete's long-term goal.
  - `shortTerm` (string): the current block's short-term target.
  - `blockReviewDate` (string, ISO date): when the current block ends.

`goals` can also be included in `write_training_block_plan` payloads at the
top level alongside the block object.

## Fuel guidance shape

Use `write_fuel_guidance` to send daily nutrition recommendations to the app.
Write fuel guidance after inspecting the day context's `latestFuelCheckIn` and
`fuelDiary` entries, as part of the morning coaching loop, or when the user
asks for nutrition recommendations.

```json
{
  "schema": "fuel_guidance.v1",
  "issuedAt": "2026-05-27T08:00:00Z",
  "validFor": "2026-05-27",
  "signal": "green",
  "signalLabel": "Gut versorgt",
  "signalSub": "Gute Basis für das heutige Training",
  "todayAdvice": "Your 18:00 leg session needs an earlier carb base: add rice or oats at lunch, then 25-35 g protein after.",
  "mealSuggestion": {
    "name": "Oatmeal with banana and whey",
    "rationale": "Quick carbs + protein 90 min before training",
    "timing": "Pre-workout"
  },
  "yesterdayRead": "Yesterday's intake was solid — 2650 kcal, 175g protein.",
  "mealIdeas": [
    { "tag": "pre-workout", "name": "Rice with chicken", "why": "Easy carbs + lean protein" },
    { "tag": "post-workout", "name": "Greek yogurt with berries", "why": "Fast protein + antioxidants" }
  ]
}
```

Valid `signal` values: `green`, `hold`, `fuel`, `deload`.

- `green`: nutrition is supporting training well.
- `hold`: nutrition is neutral, maintain current approach.
- `fuel`: the athlete should eat more or focus on specific macros.
- `deload`: reduce training intensity due to nutrition or recovery deficit.

## Nutrition analysis result shape

Use `write_nutrition_analysis_result` only when responding to a pending
nutrition-analysis request. Read the request with `get_nutrition_analysis_request`
and the meal photo, if any, with `get_blob_base64`, then echo the request's
`requestId` in the result.

```json
{
  "schema": "nutrition_analysis_result.v1",
  "requestId": "<id from the request>",
  "mealDescription": "Chicken, rice, and vegetables",
  "calories": 780,
  "protein": 48,
  "carbs": 82,
  "fat": 28,
  "bodyWeightKg": 82.0,
  "confidence": 0.7,
  "assumptions": ["Estimated ~150 g cooked rice"],
  "rationale": "Why these estimates and the target fit the context.",
  "correctionNotes": "What the user should correct if the estimate is off.",
  "target": {
    "dailyCalories": 2750,
    "protein": 175,
    "carbs": 320,
    "fat": 80,
    "goalMode": "recomposition",
    "rationale": "Training load supports maintenance."
  }
}
```

- `calories` must be greater than 0 and macros must be non-negative, or the app
  discards the result.
- `confidence` is in `0..1`. Image and text estimates are approximate, so always
  include `assumptions`.
- `target` is optional. When present, it updates the athlete's daily nutrition
  target, so only include it intentionally.

## Live chat channel shape

The chat is an append-only conversation. Each message is an object:

```json
{
  "seq": 1,
  "conversationId": "default",
  "role": "user",
  "content": "How was my long run?",
  "status": "pending",
  "createdAt": "2026-05-29T14:21:55+00:00",
  "updatedAt": "2026-05-29T14:21:55+00:00"
}
```

- `seq` (integer): monotonic id and ordering cursor. Strictly increasing.
- `role`: `"user"` (the athlete) or `"assistant"` (you).
- `content`: the message text (max 8000 characters per message).
- `status`: for a user turn, `"pending"` (not yet answered) → `"answered"`.
  For your reply, `"complete"`.

Turn lifecycle:

1. The athlete posts a message — it is `pending`.
2. `get_pending_chat_messages` returns every `pending` user turn, oldest first.
3. You answer with `write_chat_reply`, passing the user turn's `seq` as
   `inReplyToSeq`. This atomically stores your reply (`complete`) and marks the
   answered user turn(s) `answered`, so the next `get_pending_chat_messages`
   will not return them again. Without `inReplyToSeq`, all currently pending
   user turns are marked answered.

Delivery is message-level: post one complete reply per turn (there is no
token-by-token streaming yet). The app polls and renders new messages by `seq`.
Keep replies conversational and concise — this is live chat, not a coaching
document. Only call the `write_*` result tools (plans, fuel guidance) when the
athlete actually asks for app-importable output; a normal chat answer is just
`write_chat_reply`.

## Coaching notes shape

Coaching notes are your standing, self-authored planning memory: durable intent
extracted from free-text chat that should influence future plans even after the
bounded recent-chat window rolls forward. The server stores them verbatim
(validation checks only an optional string `schema`), so you own the shape. A
workable shape:

```json
{
  "schema": "coaching_notes.v1",
  "updatedAt": "2026-05-31T08:00:00Z",
  "athleteRequests": [
    {
      "text": "Move the long run to Saturday going forward.",
      "sourceSeq": 42,
      "status": "open",
      "createdAt": "2026-05-31T07:55:00Z"
    }
  ],
  "openQuestions": [
    {
      "text": "Is the left knee still sore after Tuesday's session?",
      "sourceSeq": 39,
      "createdAt": "2026-05-30T18:10:00Z"
    }
  ],
  "summary": "Wants weekend long runs and more upper-body volume; watching left knee."
}
```

- `athleteRequests`: explicit, plan-relevant asks from chat. Keep `sourceSeq`
  (the chat `seq` it came from) for traceability. Mark `status` `"addressed"`
  (or drop the entry) once a written plan reflects it, so it stops nagging.
- `openQuestions`: things you asked or could not resolve and should follow up on.
- `summary`: optional rolling one-paragraph digest for fast planner intake.

`write_coaching_notes` replaces the whole object — read with `get_coaching_notes`,
merge, write back. Record only durable, plan-relevant intent; skip routine
chit-chat.

## Planning context shape

`get_planning_context` returns one `planning_context.v1` object so daily
planning is a single read instead of eight. Each artifact slot is the latest
payload or `null`:

```json
{
  "schema": "planning_context.v1",
  "generatedAt": "2026-05-31T08:00:00+00:00",
  "dayContext": { },
  "recentLogs": [ ],
  "profile": { },
  "activeBlock": { },
  "nextDayPlan": { },
  "fuelGuidance": { },
  "nutritionAnalysis": { },
  "pendingRequests": [ ],
  "coachingNotes": { },
  "recentChat": [ ]
}
```

- `recentLogs` is lifted from `daily_snapshot.recentLogs` (the recent
  training-log digest source); `coachingNotes` is the standing notes above;
  `recentChat` is the most recent chat turns (bounded by `recentChatLimit`).
- For plan generation, treat `recentLogs`, `activeBlock`, `nextDayPlan`,
  `coachingNotes`, and `recentChat` as the recent-comparison window. Read the
  bundle immediately before planning; do not cache a variety decision across
  days. If that window is missing, novelty is unknown rather than proven.
- The bundle relays artifacts verbatim and performs no interpretation. Durable,
  interpreted requests and open questions come from `coachingNotes`, which you
  author; `recentChat` remains a bounded raw context window.
- The fuller artifacts behind some slots (full app snapshot, individual pending
  requests) remain available through their dedicated read tools when you need
  more than the latest payload.
