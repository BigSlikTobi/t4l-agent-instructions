# T4L Result Payload Shapes

Load this when constructing an app-consumed payload. Authoritative source is the
repo's `docs/exchange_contract.md`; this is the working extract. Preserve the
app's existing JSON shape from the matching request or context when one exists.

## training_block_plan

Use `write_training_block_plan` only for a complete block. Send a raw block
object or `{ "block": { ... } }`. `goals` may sit at the top level alongside the
block.

Each **block** must include: `id`, `style`, `title`, `durationWeeks`,
`currentWeek`, `weeklyFocus`, `measurableTargets`, `workouts`, `createdBy`,
`createdAt`.

Valid `style`: `rugby`, `boxer`, `hybrid`, `strengthHypertrophy`,
`conditioning`, `custom`.

Each **workout** must include: `id`, `week`, `day`, `title`, `focus`,
`rationale`, `conditioning`, and either non-empty `items` (preferred for grouped
or mixed plans) or non-empty `exercises` (simple flat plans only).

Workout structure:

- Use `exercises` only for a simple flat list.
- Use `items` for supersets/circuits. `items` may contain flat exercise items
  (`type: "exercise"`) and grouped items.
- `superset`: exactly 2 child exercises, repeated for `rounds`, alternating
  A1, B1, A2, B2. Never prescribe all sets of A before B.
- `circuit`: 3 or more child exercises in sequence, repeated for `rounds`.
  Use `circuit`, not `circle`; German UI may show `Zirkel`.
- No nested groups in v1. Groups contain exercises only.
- In groups, `rounds` is the repeated-execution source of truth; child `sets`
  may be `1`.
- `group.restSeconds` applies after the final child in each round. Child
  `restSeconds` applies between child steps and can be `0`.

Each **exercise** must include: `exerciseId`, `name`, `sets`, `reps`,
`targetLoad`, `targetRpe`, `restSeconds`, `coachCue`.

Before constructing the payload, compare it with the fresh planning context:
recent logs, accepted block, prior next-day plan, coaching notes, and recent
chat. Keep the block's primary anchors and safety constraints. On a normal day,
include one meaningful fresh element when safe; normally vary 1–2 accessories
or one format/progression lever instead of rewriting the session. A deliberate
benchmark, technique, rehab, taper, or recovery repeat is valid when `rationale`
states why it repeats and what is being measured.

Do not reuse a recent title, motto, summary, or fuel sentence word for word.
New wording alone does not make a repeated workout fresh. Exact safety and form
cues may repeat when consistent wording protects the athlete.

Optional per-exercise **mobile display** fields (add when useful — keep the
Today screen compact, push long prose to `detailNote`/`media`):

- `loadLabel` — compact chip text, e.g. `16-24 kg`
- `primaryCue` — one short row cue, 3–8 words
- `detailNote` — longer coaching explanation for the detail sheet
- `warningCue` — short pain / range-of-motion / safety cue
- `trackingMode` — `"weightAndReps"` (default, omittable) / `"repsOnly"`
  (bodyweight: push-ups, pull-ups, dips, planks) / `"timeOnly"` (easy walks,
  foam rolling, stretching, cardio)
- `targetDurationSeconds` — prescribed duration for `timeOnly`; put a
  human-readable form in `reps` (e.g. `"20 min"`)
- `media` — `explainerUrl` / `youtubeUrl` / `videoUrl` (preserve known YouTube /
  Shorts links), `setup`, `cues`, `commonMistakes`

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
  "detailNote": "Controlled eccentric. Stop adding load if depth changes.",
  "warningCue": "Stop if knee pain increases.",
  "media": {
    "setup": "Kettlebell tight to sternum, feet rooted.",
    "cues": ["Tripod foot", "Ribs down", "Drive evenly through both feet"],
    "commonMistakes": ["Losing heel pressure", "Knees collapsing inward"]
  }
}
```

```json
{
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

## next_day_plan

Use `write_next_day_plan` for a single day. Wraps a `workout` (same shape as a
block workout) plus optional coaching context. Only `workout` is required;
omitted optional fields hide the matching UI element.

```json
{
  "workout": { "...same shape as a block workout..." },
  "yesterdaySummary": {
    "headline": "Solid leg day — all sets hit at RPE 7-8",
    "highlights": ["Squat 3×8 at 80 kg felt strong", "Conditioning well tolerated"],
    "tips": ["Shoulders may be fatigued — warm up extra", "Keep RPE under 8 on presses"]
  },
  "dailyMotto": "Smooth reps build the next five kilos.",
  "goals": {
    "longTerm": "Build strength while staying athletic",
    "shortTerm": "Increase bench press 1RM by 5 kg",
    "blockReviewDate": "2026-06-15"
  }
}
```

- `yesterdaySummary` — `headline` (string), `highlights` (2–4 strings), `tips`
  (1–3 strings). Base it on yesterday's workout log, nutrition, readiness, and
  HealthKit; skip if no prior-day data.
- `dailyMotto` — short, genuine motivational phrase tied to the athlete's focus;
  do not reuse a recent motto word for word.
- `goals` — `longTerm`, `shortTerm`, `blockReviewDate` (ISO date).

## fuel_guidance

Use `write_fuel_guidance` for day-level nutrition recommendations. Always
accepted by the app, but always send a complete, useful payload — especially
when responding to a `latestFuelCheckIn` / `fuelDiary` entry.

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

Valid `signal`: `green` (nutrition supporting training), `hold` (neutral,
maintain), `fuel` (eat more / focus macros), `deload` (reduce intensity due to
nutrition or recovery deficit).

## nutrition_analysis_result

Use `write_nutrition_analysis_result` only when responding to a pending
nutrition-analysis request. Read it with `get_nutrition_analysis_request` (and
the meal photo via `get_blob_base64`), then echo the request's `requestId`.

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

- `calories` must be > 0 and macros non-negative, or the app discards the result.
- `confidence` is in `0..1`; estimates are approximate, so always include
  `assumptions`.
- `target` is optional and, when present, updates the athlete's daily nutrition
  target — include it only intentionally.
