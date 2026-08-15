# T4L Legacy Result Payload Bodies

This is the detailed source for the payload body expected by current legacy MCP
writers. It does not define coaching state or prove phone application. The only
normative coaching contract is
`../../../contracts/coaching-contract.v1.schema.json`.

Use a writer only when MCP `tools/list` advertises it. Follow the tool's declared
arguments. Do not add a coaching-contract envelope to a legacy body unless the
tool schema accepts it.

## training_block_plan

Use `write_training_block_plan` only for a complete block. Send a raw block
object or `{ "block": { ... } }`. `goals` may sit at the top level alongside the
block.

Each **block** must include: `id`, `style`, `title`, `durationWeeks`,
`currentWeek`, `weeklyFocus`, `measurableTargets`, `workouts`, `createdBy`,
`createdAt`.

`durationWeeks` and `currentWeek` are positive integers. `weeklyFocus` and
`measurableTargets` are non-empty arrays of strings, never plain text. A
complete block contains at least one workout for every week from `1` through
`durationWeeks`; the app does not generate the missing weeks.

Valid `style`: `rugby`, `boxer`, `hybrid`, `strengthHypertrophy`,
`conditioning`, `custom`.

Each **workout** must include: `id`, `week`, `day`, `title`, `focus`,
`rationale`, `conditioning`, and either non-empty `items` (preferred for grouped
or mixed plans) or non-empty `exercises` (simple flat plans only).

Workout structure:

- Choose the structure from intent. Flat work fits heavy, technical, rehab, or
  full-rest exercises. Supersets fit compatible pairs. Circuits fit safe
  three-or-more-exercise sequences. A workout may mix flat and grouped items.
- Use `exercises` only for a simple flat list.
- Use `items` for supersets/circuits. `items` may contain flat exercise items
  (`type: "exercise"`) and grouped items.
- `superset`: exactly 2 child exercises, repeated for `rounds`, alternating
  A1, B1, A2, B2. Never prescribe all sets of A before B.
- `circuit`: 3 or more child exercises in sequence, repeated for `rounds`.
  Use `circuit`, not `circle`; German UI may show `Zirkel`.
- No nested groups in v1. Groups contain exercises only.
- In groups, `rounds` is the repeated-execution source of truth; child `sets`
  is `1` or omitted. Do not use child `sets` to repeat grouped work.
- `group.restSeconds` applies after the final child in each round. Child
  `restSeconds` applies after a non-final child before the next child step and
  can be `0`. It is not rest between sets.

Each **exercise** must include: `exerciseId`, `name`, `sets`, `reps`,
`targetLoad`, `targetRpe`, `restSeconds`, `coachCue`, and nested `media`.

Before construction, run the state, freshness, progression, and review procedure
in `../../../docs/coaching_setup.md`. A full block is always review-required.

Per-exercise **mobile display** fields. Keep the Today screen compact and push
long prose to `detailNote`/`media`:

- `loadLabel` — compact chip text, e.g. `16-24 kg`
- `primaryCue` — one short row cue, 3–8 words
- `detailNote` — longer coaching explanation for the detail sheet
- `warningCue` — short pain / range-of-motion / safety cue
- `trackingMode` — `"weightAndReps"` (default, omittable) / `"repsOnly"`
  (bodyweight: push-ups, pull-ups, dips, planks) / `"timeOnly"` (easy walks,
  foam rolling, stretching, cardio)
- `targetDurationSeconds` — prescribed duration for `timeOnly`; put a
  human-readable form in `reps` (e.g. `"20 min"`)
- `media` — required. Generate `explainerUrl` in the exact canonical form
  `https://www.youtube.com/shorts/<videoId>`. Normal YouTube `watch` links,
  `youtu.be`, other hosts, web pages, and legacy `youtubeUrl`/`videoUrl` aliases
  are invalid for generated plans. `setup`, `cues`, and `commonMistakes` must
  be non-empty.

Never invent a URL or video ID. Verify the Short for the exact variation during
the current run or use a trusted, current catalog supplied in accepted context.
A verified YouTube result may supply the ID, but store the canonical `/shorts/`
form. If verification is impossible, stop before the writer and report the
missing Shorts lookup capability.

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
    "explainerUrl": "https://www.youtube.com/shorts/mF5tnEBrdkc",
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
        {
          "exerciseId": "hand_release_push_up",
          "name": "Hand-Release Push-Up",
          "sets": 1,
          "reps": "10",
          "trackingMode": "repsOnly",
          "targetLoad": "bodyweight",
          "targetRpe": 7,
          "restSeconds": 0,
          "coachCue": "Brace and move as one line.",
          "media": {
            "explainerUrl": "https://www.youtube.com/shorts/qFFtrj0mdBQ",
            "setup": "Hands just outside shoulders, body in one line.",
            "cues": ["Brace before lowering", "Press the floor away"],
            "commonMistakes": ["Hips sagging", "Losing the hand release"]
          }
        },
        {
          "exerciseId": "double_dumbbell_row",
          "name": "Double Dumbbell Row",
          "sets": 1,
          "reps": "12",
          "targetLoad": "moderate",
          "targetRpe": 7,
          "restSeconds": 0,
          "coachCue": "Pull elbows back without shrugging.",
          "media": {
            "explainerUrl": "https://www.youtube.com/shorts/t7VDDNKBNx8",
            "setup": "Hinge with both dumbbells below the shoulders.",
            "cues": ["Keep the torso still", "Pull elbows toward the hips"],
            "commonMistakes": ["Shrugging", "Standing up during the row"]
          }
        }
      ]
    }
  ]
}
```

```json
{
  "exerciseId": "air_squat",
  "name": "Air Squat",
  "sets": 3,
  "reps": "12-15",
  "trackingMode": "repsOnly",
  "targetLoad": "Bodyweight with repeatable depth.",
  "targetRpe": 7,
  "restSeconds": 60,
  "coachCue": "Keep the whole foot rooted and drive the knees out.",
  "primaryCue": "Whole foot rooted",
  "warningCue": "Stop if knee pain increases.",
  "media": {
    "explainerUrl": "https://www.youtube.com/shorts/C_VtOYc6j5c",
    "setup": "Feet around shoulder width with toes slightly out.",
    "cues": ["Brace", "Knees track over toes", "Stand tall"],
    "commonMistakes": ["Heels lifting", "Knees collapsing inward"]
  }
}
```

For a circuit, use the same child exercise shape with three or more children:

```json
{
  "type": "circuit",
  "groupId": "circuit_1",
  "title": "Conditioning Circuit",
  "rounds": 3,
  "restSeconds": 90,
  "exercises": [
    { "...": "full exercise with required media" },
    { "...": "full exercise with required media" },
    { "...": "full exercise with required media" }
  ]
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
  (1–3 strings). Base it only on fresh phone-accepted context; skip it when the
  prior-day data or provenance is missing.
- `dailyMotto` — short, genuine motivational phrase tied to the athlete's focus;
  do not reuse a recent motto word for word.
- `goals` — `longTerm`, `shortTerm`, `blockReviewDate` (ISO date).

Nutrition and fuel payloads are intentionally absent. The coach is
training-and-recovery only. It must not analyze meals or generate calorie,
macro, fluid, electrolyte, supplement, weight, or body-composition guidance.
