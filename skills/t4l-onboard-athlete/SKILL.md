---
name: t4l-onboard-athlete
description: Use when a T4L athlete's accepted long-term goal or current block target is missing. Confirms a goal brief before any plan proposal.
---

# Onboard a T4L Athlete

Requires `../../contracts/coaching-contract.v1.schema.json` and a fresh
accepted-state response from `get_planning_context`.

## Discover

Ask only for gaps that accepted phone state does not already answer:

- long-term goal;
- next 1–4 week block target and why it matters;
- success test and review date;
- schedule, session length, equipment, and environment;
- pain, injury, recovery, and hard movement limits;
- coaching style and useful amount of familiarity versus variety.

Do not ask for food, meal, calorie, macro, fluid, electrolyte, supplement,
weight, or body-composition goals. Refer individualized questions in those
areas to a registered dietitian or clinician.

If the athlete gives only a long-term goal, recommend a specific short block.
Do not generate the plan until the athlete confirms the goal brief.

## State boundary

The confirmed brief supports one pending athlete setup draft. After the athlete
explicitly confirms the summary in chat, call `write_athlete_setup_draft` once
with result kind `athlete_setup_draft`. The strict payload is:

```json
{
  "schema": "athlete_setup_draft.v1",
  "draftId": "setup_01J...",
  "createdAt": "2026-08-11T09:10:00Z",
  "source": {
    "conversationId": "default",
    "confirmedMessageSeq": 12,
    "confirmedAt": "2026-08-11T09:09:55Z"
  },
  "profile": {
    "name": "Tobi",
    "goal": "Build strength and train pain-free",
    "trainingDays": 4,
    "sessionMinutes": 60,
    "equipment": ["fullGym"],
    "constraints": ["No painful pressing"],
    "preferences": ["Compound lifts", "Short finishers"]
  },
  "goals": {
    "longTerm": "Build durable strength",
    "shortTerm": "Complete four consistent weeks",
    "blockWeeks": 4,
    "successTest": "Finish all planned sessions without pain",
    "reviewDate": "2026-09-08"
  },
  "hardLimits": ["Stop any movement that causes sharp pain"],
  "nutritionPreferences": [],
  "coachingStyle": "Direct and concise",
  "confirmation": {
    "summary": "Four gym days, 60 minutes, strength focus, no painful pressing.",
    "confirmed": true
  }
}
```

Required top-level fields are exactly `schema`, `draftId`, `createdAt`,
`source`, `profile`, `goals`, `hardLimits`, `nutritionPreferences`,
`coachingStyle`, and `confirmation`; `requestId` is optional. `draftId` must be
non-empty and stable for this logical draft. `source.confirmedMessageSeq` is an
integer of at least 1 and `source.confirmedAt` is an ISO timestamp. The profile
requires `goal`, `trainingDays` (1–7), `sessionMinutes` (10–240), `equipment`,
`constraints`, and `preferences`. Goals require `longTerm`, `shortTerm`,
`blockWeeks` (1–4), and `successTest`. Confirmation must contain the exact
summary and `confirmed: true`. Do not add unknown fields.

`nutritionPreferences` remains required only for compatibility with the
existing phone wire schema. Always send an empty array. Never use it for
guidance or collect nutrition details during onboarding.

The writer result proves only that `athlete_setup_draft.v1` is pending phone
review. It is not accepted state. Never say setup was saved, accepted, applied,
or synced from this result alone. Wait until a fresh `get_planning_context`
shows the phone-owned accepted setup at a new `contextRevision`.

The confirmed brief may support a contract proposal only after the phone
accepts and syncs it in a fresh planning context and creates the matching
current request. Chat confirmation is not accepted state and does not create
standing auto-apply consent.

Use only the phone's canonical equipment IDs in `profile.equipment`:
`bodyweight`, `dumbbells`, `barbell`, `curlBar`, `kettlebells`, `bands`,
`bosu`, `fullGym`, `machines`, `cableMachine`, `pullUpBar`, `bench`, and
`squatRack`. Normalize clear spacing, hyphen, or underscore variants to these
IDs. Ask the athlete when an equipment term is unknown; never invent or
silently drop it.

Do not write sensitive data into harness memory. Do not call a fictional memory
or wiki tool. Until phone-owned evidence appears in planning context, do not
emit a contract proposal or claim persistence.

## Next

After phone acceptance, acknowledge the fresh `contextRevision`, recap the
short-term goal and hard limits in 2–4 lines, say plans are review-only
proposals, and continue with the current training-block request. Use
`t4l-coach-daily`. Use `t4l-write-results` before a plan result write. Full
blocks remain review-required even when the athlete has standing consent for
minor daily changes. A contract proposal also needs a phone-authored current
request and its `requestId`; never invent one from chat.
