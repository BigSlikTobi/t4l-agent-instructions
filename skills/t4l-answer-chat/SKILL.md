---
name: t4l-answer-chat
description: Use for a pending T4L chat turn. Binds work to one athlete message, uses a claim when supported, and preserves newer messages.
---

# T4L Answer Chat

Requires `../../contracts/coaching-contract.v1.schema.json`, the chat rules in
`../../docs/exchange_contract.md`, and accepted context from
`get_planning_context`.

## Concurrency gate

Use multiple workers only when MCP advertises atomic claim/lease and idempotent
reply support. A pending queue read is not a claim.

If only `get_pending_chat_messages` and `write_chat_reply` exist, require one
externally serialized consumer for the conversation, backed by a single
deployment or external lock. If exclusive ownership cannot be proved, do not
write. Overlapping polls can double-reply.

## One-turn routine

1. Claim the oldest athlete message when a claim tool exists. Otherwise, in
   single-worker mode, select the oldest pending message and treat it as the
   only local job.
2. Capture its exact content, conversation ID, message ID/`seq`, claim ID,
   claim expiry, and reply idempotency key when those fields exist.
3. Call `get_planning_context` fresh. Do not switch to a newer chat message
   while reading context or reasoning.
4. Answer the captured question. Use synced facts only. No live mid-set claim
   unless the accepted context contains a fresh phone-sourced set event.
5. Post the answer against the exact claimed message. In the legacy tool, always
   pass its original `seq` as `inReplyToSeq`.
6. Finish or release the exact claim when the protocol supports it. Then take
   the next message.

Never omit `inReplyToSeq` in legacy mode. Never acknowledge or mark a newer,
unrelated athlete message as part of the current job.

## Reply style

- Keep it short and direct.
- Separate synced facts from assumptions.
- Do not invent health, history, or current-set data.
- A normal chat answer uses `write_chat_reply`, not a plan-result writer.
- A requested plan remains a proposal and follows review rules. A chat `seq` is
  not a contract `requestId`; do not emit the proposal until planning context
  contains the matching phone-authored current request.
- Pain, injury, dizziness, illness, or push-through questions get a conservative
  answer and escalation when needed.
- Stay inside training and recovery. Never provide food, meal, calorie, macro,
  fluid, electrolyte, supplement, weight, or body-composition advice,
  calculations, targets, or inferred deficiencies or diagnoses. Reply with the
  fixed scope boundary and refer individualized questions to a registered
  dietitian or clinician.

## Escalation

Pass the captured question and all claim/message IDs directly to the heavy
worker. Do not re-poll the queue to rediscover it.

If an acknowledgement is posted, bind it to the original message. Bind the
final answer to that same message too. The arrival of a newer message does not
change the target.

Legacy chat has no durable processing state. An acknowledgement can remove a
turn from the pending queue before the heavy answer exists. Prefer one final
reply in legacy mode. If an acknowledgement is unavoidable, keep the worker
alive through the final write and report a real failure status if reasoning
fails. Do not leave silence.

## Retry and idempotency

- With an idempotency key, retry the same logical reply with the same key and
  content digest.
- New content gets a new key.
- A duplicate key with different content is a conflict.
- Without idempotency, do not blindly retry an ambiguous timeout. Inspect fresh
  planning/chat evidence first. If delivery remains unknown, escalate to the
  athlete or operator instead of risking a duplicate.
- If a claim expires, do not write under it. Reclaim through the protocol or
  leave the message for another worker.
