# T4L Agent Instructions

This repository connects an existing OpenClaw coach to the T4L iPhone app.

## Quick install

Paste this one line into the OpenClaw agent you already use:

```bash
curl -fsSL https://bigsliktobi.github.io/t4l-agent-instructions/install.sh | bash
```

That is all. The agent executes it, installs the pinned T4L runtime, reads the
runbook, inspects its own host, and continues the setup. The user does not need
to provide package names, flags, tokens, or configuration.

The agent should need you only if:

- it cannot safely choose your public hostname;
- the host needs a real administrator approval;
- the iPhone shows the final `/t4l connect XXXX-XXXX` pairing command.

No second account, second OpenClaw agent, API-key form, or Tailscale network is
needed for a normal public VPS.

## What the installer keeps unchanged

It keeps the existing OpenClaw agent, model, provider, credentials, channels,
dashboard, reverse proxy, and unrelated services.

The coach instructions are packaged inside `t4l-agent`. The host runbook remains
available in [INSTALL.md](INSTALL.md) for inspection, but the user does not need
to read or paste it.
