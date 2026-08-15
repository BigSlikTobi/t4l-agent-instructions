# T4L Agent Skills

Portable coaching adapters. They follow the `SKILL.md` convention.

The only normative coaching contract is
`../contracts/coaching-contract.v1.schema.json`. Skills must not redefine its
state, consent, review, freshness, or retry semantics.

| Skill | Use |
|---|---|
| `t4l-onboard-athlete` | Confirm missing goals and constraints. |
| `t4l-coach-daily` | Make a daily decision from accepted planning context. |
| `t4l-write-results` | Validate and store a legacy proposal body. |
| `t4l-answer-chat` | Answer one pending athlete turn; claim it when supported. |

## Portability

- Frontmatter stays limited to `name` and `description`.
- Tool availability is discovered through MCP `tools/list`; skills do not
  hard-code `allowed-tools`.
- `t4l-write-results` includes a dependency-free legacy payload validator.
- The setup capability gate still applies after a skill is installed.

## Install

Keep the repo layout intact. Register `skills/` as a skill source or symlink its
skill folders from this checkout. Do not copy one folder alone; adapters use the
single contract and procedure docs elsewhere in the repo. Refresh existing
links instead of duplicating them. Restart only if the harness scans skills at
startup and files changed.

## Tests

From the repo root:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```
