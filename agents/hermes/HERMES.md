# T4L Self-Hosted Server Startup

Before coaching, read `docs/setup_instruction.md` first and follow the docs it
points to in order. Verify or start `t4l-server`, connect through MCP, wait for
fresh app context, inspect the available context/tools, then begin the T4L
coaching workflow.

Do not coach from memory alone and do not generate server implementation code.

## Delegation (head coach + specialist sub-agents)

Hermes supports real sub-agents via `delegate_task`. The **t4l-coach-committee**
skill uses them: in committee mode the head coach fans the five specialist
coaches out as concurrent sub-agents, collects their positions, applies the
conflict ladder, and writes the converged plan. To enable this, ensure your
Hermes `config.yaml` carries a `delegation:` block — **merge** these keys into
your existing config (do not overwrite the whole file):

```yaml
delegation:
  orchestrator_enabled: true
  max_concurrent_children: 5   # so all 5 specialists fan out in one wave (default 3 → 3+2)
  max_spawn_depth: 1           # flat: head coach → 5 leaf specialists, no nesting
```

Keep these rules in mind (they match how the committee skill is written):

- **Specialists are advisory; the head coach owns all MCP I/O.** A sub-agent
  starts with zero context and a restricted toolset (`clarify`, `memory`,
  `send_message`, MCP writes are not available to it). The head coach reads
  `get_planning_context`, passes each specialist what it needs inline, collects
  the summaries, and performs every `write_*` via **t4l-write-results**.
- **Delegate only the heavy committee path.** Routine daily progress/hold and
  fast in-app chat replies stay a single-specialist **lens on the current model —
  no sub-agent spawn** — so chat latency is unaffected.

If delegation is disabled or unavailable, the committee skill falls back to
single-agent role-play of the same five coaches; behaviour and output are
identical.
