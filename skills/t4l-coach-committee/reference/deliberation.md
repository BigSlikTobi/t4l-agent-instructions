# Committee Deliberation Protocol

How the head coach runs the five specialists (`reference/coaches.md`) and
converges them into one decision. The mechanism differs by harness; the protocol
and the output do not.

## Protocol

1. **Frame.** From `get_planning_context`, assemble the facts each specialist
   needs (goal, block target + `style`, week/next workout, recent performance and
   recovery, constraints, nutrition context, coaching notes/recent chat). Draft a
   **straw-man leading plan** — your best first guess — for the coaches to react
   to. A concrete target sharpens the debate.
2. **Convene** the five specialists (see "Convening" below). Each returns, in a
   structured summary:
   - its **position** — the recommendation from its lens, and
   - its **biggest objection** to the straw-man leading plan (the debate rule —
     every coach must name one even if minor).
3. **Debate** one round on the strongest objections. If two coaches genuinely
   conflict, re-consult **only those coaches** with the others' positions added
   to their context; do not re-run the whole committee. Keep it bounded — at most
   one extra targeted round — so latency and cost stay in check.
4. **Decide** with the conflict ladder, then **converge** to one plan **plus a
   recorded dissent (minority report)**: name which coach disagreed and why, in a
   line the athlete can see. Hand the converged plan to **t4l-write-results**.

## Safety-first conflict ladder

Apply in order; the first rule that resolves the conflict wins.

1. **Veto — safety and hard constraints.** The **physiotherapist** (pain, injury,
   illness, dizziness, red flags) and any **hard athlete constraint** (declared
   injury, movement to avoid, schedule/equipment limit) can veto. A veto is
   absolute; route around it, never through it.
2. **Lead coach gets priority.** The coach who owns the current block target
   leads; conflicts between non-safety qualities resolve in the lead's favour.
   Lead-coach map, keyed on the block `style` enum documented by the
   **t4l-write-results** skill (`reference/payload-shapes.md` inside that
   installed skill):

   | block `style` | lead coach |
   |---|---|
   | `strengthHypertrophy` | strength |
   | `conditioning` | stamina |
   | `rugby` / `boxer` / `hybrid` | head coach picks the **dominant demand** of the block's stated focus |
   | `custom` | by the **stated target** (mobility/flexibility/movement-quality → coordination; otherwise the closest specialist) |

   There is no dedicated `mobility` style — a mobility block is a `custom` block
   led by coordination.
3. **Others adapt.** Remaining coaches fit their work around the lead's plan
   (e.g. conditioning placed to protect fresh legs for a strength lead; mobility
   prep sequenced before loaded work).
4. **Head coach decides and records dissent.** You make the final call and write
   the minority report. Ties and genuinely close calls are yours to break.

## Convening the specialists

### Primary: real sub-agents on Hermes (`delegate_task`)

Fan all five out in **one** `delegate_task` batch so they run concurrently:

- `tasks`: five task objects, one per coach.
- For each task: `goal` = that coach's brief from `reference/coaches.md` + the
  instruction to return *position + biggest objection*; `context` = the athlete
  slice from `get_planning_context` + the straw-man leading plan. Pass everything
  inline — sub-agents start with **zero** prior knowledge.
- `role`: `"leaf"` (specialists do not delegate further).
- `toolsets`: a **read-only** set (e.g. `["file"]`). Specialists are advisory:
  they reason and summarize; they do **not** touch MCP, ask the athlete, or write
  results — the head coach does all of that after collecting the summaries.

Ensure the Hermes `config.yaml` enables delegation with room for five children:

```yaml
delegation:
  orchestrator_enabled: true
  max_concurrent_children: 5   # so all 5 specialists run in one wave (default 3 → 3+2)
  max_spawn_depth: 1           # flat: head coach → 5 leaves, no nesting
```

See `agents/hermes/HERMES.md` for enabling this on the Hermes harness.

### Fallback: single-agent role-play

On a harness without delegation, role-play the same five briefs **sequentially**
in one agent — adopt each coach's lens in turn, write down its position and
objection, then apply the identical ladder. Behaviour and output match the
delegated path; only the mechanism differs. This keeps the skill portable across
harnesses that lack a delegation feature.

## Daily escalation triggers (from `t4l-coach-daily`)

The head coach runs the daily loop and consults a single specialist **lens** for
routine calls (fast, no committee, no spawn). Convene the **full committee** only
when the day's decision is significant:

- `deload`, `rest`, or a pain-driven `substitute`;
- a detected plateau or regression;
- the block **review date** is reached;
- the athlete asked for a re-eval (from coaching notes / recent chat).

Otherwise — routine `progress`/`hold` — stay in the fast single-lens path.
