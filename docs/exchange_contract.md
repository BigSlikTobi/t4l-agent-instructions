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

Keep `targetLoad` and `coachCue` complete enough for logs, review, and future
agents. Use `loadLabel` and `primaryCue` to keep the phone workout screen
compact. If display fields are omitted, the app falls back to `targetLoad` and
`coachCue`, so long prose there will make the Today screen harder to scan.

Exercises may include `media` with:

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
