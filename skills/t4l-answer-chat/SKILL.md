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

## Liveness

A run answers the backlog once. The chat only feels live if this routine runs on
a short interval (a watch loop or cron on the agent's host). See "Making chat
live (scheduling)" in `docs/coaching_setup.md`.
