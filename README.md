# T4L Agent Instructions

This repository connects an existing OpenClaw coach to the T4L iPhone app.

## The only message the user sends

Send this to the OpenClaw agent you already use:

> Read https://github.com/BigSlikTobi/t4l-agent-instructions and follow
> `INSTALL.md` from start to finish. Connect the existing OpenClaw agent I am
> talking to with T4L. Do the host work yourself. Preserve my current agent,
> model, provider, credentials, channels, dashboard, and other services. Ask me
> only if the runbook says a person must decide or act.

That is all. Do not paste commands, package names, tokens, or configuration into
the chat or the phone.

The agent should need you only if:

- it cannot safely choose your public hostname;
- the host needs a real administrator approval;
- the iPhone shows the final `/t4l connect XXXX-XXXX` pairing command.

No second account, second OpenClaw agent, API-key form, or Tailscale network is
needed for a normal public VPS.

## For the installing agent

Read and execute [INSTALL.md](INSTALL.md). Do not turn it into terminal homework
for the user.

The coach instructions are packaged inside `t4l-agent`. Do not restore or load
the old duplicate instruction bundle from this repository's history.
