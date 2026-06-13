---
name: t4l-onboard-athlete
description: Use when a T4L athlete's long-term goal or current block target is missing or unclear. Runs goal discovery and produces a Coaching Contract before any training plan is written.
---

# Onboard a T4L Athlete (Goal Discovery)

Run this **before** generating any plan when the long-term goal or the current
short-term block target is missing or unclear. Do not jump straight to a plan.
The outcome must be a clear long-term goal **plus** a current short-term block
target.

## 1. Discover (ask, or infer from context and confirm)

- **Long-term goal** — the months-scale outcome: strength, athleticism,
  flexibility, body composition, sport performance, or health.
- **Current block target** — the focus for the next 1–4 week cycle.
- **Why this block matters** — how the short-term focus serves the long-term goal.
- **Success criteria** — measurable/observable proof the block worked.
- **Schedule** — training days, session length, hard calendar constraints.
- **Equipment & environment** — what can actually be used.
- **Constraints** — injuries, pain, movements to avoid, recovery limits.
- **Nutrition context** — foods, timing, digestion, hydration, preferences, and
  whether the athlete wants food-based advice vs fixed calorie/macro targets.
- **Preference context** — coaching language, exercise likes/dislikes, and how
  much explanation they want.

If the athlete gives only a long-term goal, **recommend** a specific, time-boxed
short-term block. Example: long-term "move better, less stiffness" → a 2-week
mobility block with daily range-of-motion checkpoints.

## 2. Confirm a Coaching Contract

After the athlete confirms, summarize compactly:

- Long-term goal
- Current block target
- Block length and review date
- Success criteria
- Training constraints
- Nutrition guidance style
- Follow-up rule

**Follow-up rule:** when the block length ends, review performance, recovery,
nutrition, and adherence, then recommend the next short-term goal. Never
silently continue the old target without reviewing it.

## 3. Persist (only what's allowed)

- If the app exposes `memoryWiki`, ask the athlete to save the confirmed
  long-term goal and current block target as active memories (categories:
  `goal`, `constraint`, `preference`). If you cannot write memories, carry them
  as explicit chat context.
- If the harness supports persistent memory (project memory, `SOUL.md`, etc.),
  store only a compact coaching identity: role, long-term goal, current block
  target, block review date, hard constraints, nutrition style, and the rule
  that **app + MCP context remain the source of truth**.
- Do **not** store sensitive health, injury, nutrition, or body data without
  explicit consent. Never treat stored memory as fresher than app context.

## Next

Once the goal and block target are set, design the **first training block** with
**t4l-coach-committee** (committee mode) — the head coach convenes the specialist
coaches to shape the block rather than drafting it from a single perspective.
After the block exists, use the **t4l-coach-daily** skill for the daily decision
loop. When you produce app-importable JSON, use **t4l-write-results**.
