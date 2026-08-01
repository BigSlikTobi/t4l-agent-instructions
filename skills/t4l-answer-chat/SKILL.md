---
name: t4l-answer-chat
description: Use when the athlete has sent in-app chat messages. Drains pending chat via get_pending_chat_messages and replies with short, workout-aware answers via write_chat_reply.
---

# T4L Answer Chat

The athlete chats with you **inside the app** — this replaces any third-party
chat app. The self-hosted server relays the conversation over MCP. This skill is
the **answer-time** behavior: how to reply well to a chat turn. The build/run
side of the chat loop (model split, warm-loop hosting, polling, routing,
freshness) lives in `docs/coaching_setup.md` — read it when building or tuning
the loop, not on every reply.

Payload fields and the turn lifecycle: `docs/exchange_contract.md`
("Live chat channel shape").

## Routine

1. `get_pending_chat_messages` → empty means nothing to do.
2. For each pending message, **oldest first**:
   - Read `get_day_context` (and `get_profile` / `get_app_snapshot` if needed),
     plus recent history (`daily_snapshot:latest.recentLogs`), so the reply
     reflects the athlete's real, current state — including a **live workout in
     progress**. Re-read these each turn; never answer from a cached copy.
   - Write a short, direct reply to the actual question.
   - Post with `write_chat_reply`, passing the message's `seq` as `inReplyToSeq`
     — that marks the turn answered so it is not returned again.
3. **After replying**, if the turn carried durable, plan-relevant intent — an
   explicit request, or a question you could not resolve — fold it into the
   standing coaching notes: `get_coaching_notes` → merge (keep the chat `seq` as
   `sourceSeq`) → `write_coaching_notes`. This keeps important intent available
   after the bounded recent-chat window rolls forward. Do it **after** the reply
   so it adds no latency, and only when there is something durable — skip
   chit-chat.

## How to answer

- **Conversational, not a document.** Tight, direct, no boilerplate. This is
  live chat.
- **Sound current.** Do not recycle stock openings, praise, apologies, or
  sign-offs from recent chat. Lead with the fact that matters now. Repeat exact
  safety wording only when consistency is useful.
- **Workout-aware.** Ground answers in the synced context and recent logs, so
  "how was my run?" / "what about Wednesday?" reflect real data.
- **Never dead-end.** Do not tell the athlete "I couldn't find that" or "send me
  what you did". If you lack the data or the turn needs deep analysis, that is an
  **escalation**, not a reply — post a brief "give me a second…" and hand the
  question (in memory, with its `seq`) to the reasoning model, which then posts
  the real answer. Only after actually checking the full history/tools may you
  say a fact genuinely isn't in the synced data — and say specifically what you
  checked. Never invent health/log data.
- **An escalation always concludes.** Once the ack is posted the turn leaves the
  pending queue, so you own delivering the result: always `write_chat_reply` the
  reasoning model's answer; if it errors, post a real status, never silence.
- **Don't write plans from a casual question.** A chat answer is just
  `write_chat_reply`. Switch to **t4l-write-results** only when the athlete asks
  for app-importable output, and ask before writing app-consumed JSON that
  changes goals, constraints, training direction, or nutrition targets.
- **Capture durable intent, not chit-chat.** A reply answers the moment; the
  *plan* needs the intent. Fold explicit requests and open questions into
  coaching notes (`write_coaching_notes`) so the daily loop acts on them —
  "how was my run?" or "thanks" needs no note.
- **Safety first.** Pain, injury, dizziness, illness, or "should I push through
  this?" get a careful, conservative answer (escalate when unsure) — never a
  breezy reply.
- **Safe to run often.** Answering a turn marks it `answered`, so repeated runs
  never double-reply.

Routing (answer-or-escalate, the structured escalate signal, history digest),
two-tier ack/escalate mechanics, model split, and loop hosting are all detailed
in `docs/coaching_setup.md`.
