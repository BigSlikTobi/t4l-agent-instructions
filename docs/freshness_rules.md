# Freshness Rules

- Treat MCP `get_day_context` as the primary current-day context.
- Do not coach (first session of the day, plans, reviews) until current context
  is on the server. The app auto-pushes `day_context` **and** `daily_snapshot`
  after each workout, reflection, and fuel event, and on the manual "Context
  Push"; if nothing has been synced this session, ask the user to open the app
  and push.
- For in-app chat, re-read the artifacts **each turn** — `get_day_context` for
  today and `daily_snapshot:latest` for recent history (`recentLogs`). Do not
  cache them for the life of a warm chat loop, or you will answer from stale
  data after the athlete logs new work. See "Routing" in `coaching_setup.md`.
- For daily planning, freshness includes a **recent-comparison window**, not
  only today's readiness. Immediately before prescribing, read
  `get_planning_context` and compare the candidate with `recentLogs`, the
  accepted `activeBlock`, the prior `nextDayPlan`, coaching notes, and recent
  chat. Check exercise order, prescription, session format, title, motto, cues,
  summary language, and fuel advice. Do not cache this comparison across days.
- Freshness is bounded by the app's last push: a set logged *mid-workout* is not
  on the server until the workout is completed, and `recentLogs` holds only the
  ~10 most recent logs. Treat data outside that window as unavailable.
- Coaching notes (`get_coaching_notes`, also bundled in `get_planning_context`)
  are agent-authored, not app-synced: they are current as of the last chat turn
  you captured into them, not gated by an app push. `get_planning_context` is
  otherwise only as fresh as its underlying artifacts (same push bound as above).
- Missing HealthKit, nutrition, or workout fields are unknown, not zero.
- Missing recent history is also unknown. Do not claim that a session or phrase
  is new when the available comparison window cannot show that. Use a safe,
  block-consistent choice and say that the history check was limited when it
  matters.
- If context is stale or server sync fails, ask the user to open the app,
  reconnect the server, and push fresh context.
