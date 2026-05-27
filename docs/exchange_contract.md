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
- non-empty `exercises`

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
  "dailyMotto": "Consistency beats intensity.",
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
- `dailyMotto` (optional, string): short motivational phrase for the day.
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
  "todayAdvice": "Focus on carbs before and protein after your leg session today.",
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
