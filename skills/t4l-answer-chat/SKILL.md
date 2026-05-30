---
name: t4l-answer-chat
description: Use when the athlete has sent in-app chat messages. Drains pending chat via get_pending_chat_messages and replies with short, workout-aware answers via write_chat_reply.
---

# T4L Answer Chat

The athlete chats with you **inside the app** — this replaces any third-party
chat app. The self-hosted server relays the conversation over MCP. Your job
here is fast, conversational replies, not coaching documents.

Payload fields and the turn lifecycle are in `docs/exchange_contract.md`
("Live chat channel shape").

## Routine

1. Call `get_pending_chat_messages`. Empty → nothing to do.
2. For each pending message, **oldest first**:
   - Read `get_day_context` (and `get_profile` / `get_app_snapshot` if needed)
     so the reply reflects the athlete's real, current state — including the
     **live workout in progress** when present (current exercise, sets/reps
     logged so far). This is what lets you coach mid-set.
   - Write a short, direct reply. Answer the actual question; no boilerplate.
   - Post it with `write_chat_reply`, passing the message's `seq` as
     `inReplyToSeq`. That marks the turn answered so it is not returned again.

## Rules

- **Conversational, not a document.** Keep it tight — this is live chat.
- **Missing data is unknown, not zero.** Don't invent health/log data; if you
  need something the context doesn't have, ask in the reply.
- **Don't write plans from a casual question.** A normal chat answer is just
  `write_chat_reply`. Only switch to **t4l-write-results** (`write_next_day_plan`,
  `write_training_block_plan`, `write_fuel_guidance`) when the athlete actually
  asks for app-importable output, and still ask before writing app-consumed JSON
  that changes goals, constraints, training direction, or nutrition targets.
- **Safe to run often.** Answering a turn marks it `answered`, so repeated runs
  never double-reply.

## Two-tier replies (fast ack, then escalate)

If you ack a heavy turn on the fast model and hand the real work to a strong
model, beware the trap: **posting the ack marks the user turn `answered`**, so
`get_pending_chat_messages` is then empty. The heavy worker must receive the
question **in memory** — never re-poll the queue for it — and then post the real
answer as a fresh `write_chat_reply`.

```text
heavy turn (seq=N, text=Q):
  write_chat_reply("On it — give me a minute. 🧠", inReplyToSeq=N)
  answer = strong_model(Q, full_context)   # Q carried in memory, not re-fetched
  write_chat_reply(answer)                  # fresh reply; queue is already empty
```

Also: read `get_day_context` on the fast path too (don't go workout-blind), keep
the ack distinct from any error/fallback string, escalate safety/pain/injury
turns rather than answering them fast, and test the heavy path end to end — a
fast-path-only test passes even when escalation is broken. Full detail in
"Two-tier replies" in `docs/coaching_setup.md`.

## Liveness and speed

A run answers the backlog once. The chat only feels live if this routine runs on
a short interval. **Prefer one warm, long-lived process that loops internally**
(connect to MCP once, then poll every ~2–4 s) over re-launching the harness per
reply — re-launching pays process-boot + doc-reading + MCP-handshake on every
turn, which is what makes replies take tens of seconds.

If you must re-invoke per turn, scope each invocation to **answering only** — do
not re-run the one-time setup or re-read the setup docs just to answer a chat
turn.

Run the chat loop on a **fast, low-reasoning model** (Haiku / mini / Flash-class)
with a small token budget — conversational replies do not need heavy reasoning,
and a reasoning-heavy model spends most of its latency thinking before it
answers. Keep your strong reasoning model for plan generation
(**t4l-write-results**), not for chat. See "Model choice" and "Making chat live
(scheduling)" in `docs/coaching_setup.md`.
