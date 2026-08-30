# Install T4L for the current OpenClaw agent

You are the host agent. Execute this runbook yourself. Do not ask the user to
copy commands, edit files, install packages, or handle secrets.

## Goal

Connect the existing OpenClaw agent from this conversation to the T4L iPhone
app.

Keep the existing:

- agent and profile;
- model, provider, reasoning mode, credentials, tools, and channels;
- dashboard, reverse proxy, DNS, and unrelated services such as n8n.

Create only one pinned T4L plugin, one loopback connector service, and one
narrow HTTPS route for the phone. Do not create another account or agent. Do
not expose the OpenClaw dashboard.

This runbook supports OpenClaw on a Linux VPS with systemd and a public HTTPS
hostname. It does not support Hermes, a LAN-only host, or a Tailscale-only host.
Tailscale is not needed for a normal public VPS.

## Fixed releases

Use these releases unchanged:

- OpenClaw `>=2026.7.1-2` and `<2027.0.0`
- `@t4l-trainer/openclaw-t4l-connect@0.4.0`
- `t4l-agent==0.4.0`
- `t4l-server==0.9.0`
- Python 3.11 or newer

Never patch an installed package or install from a branch.

## 1. Inspect the host

Find these values yourself:

- the absolute OpenClaw executable;
- the current conversation's agent ID, display name, and profile;
- OpenClaw's home, state directory, and config file;
- the active Gateway systemd service, system or user scope, and loopback port;
- the exact verified owner identity as `channel:account:sender`;
- one public hostname owned by the user and pointing to this VPS;
- the existing reverse proxy and its route to the loopback Gateway.

Use the agent from this conversation. Do not choose a different one because it
looks easier.

For authenticated OpenClaw webchat with no explicit account or sender IDs, use
the connector fallback `webchat:gateway:operator-admin`. For every other
channel, use OpenClaw's verified values. Never invent them.

Ask the user one short question only when more than one owned public hostname
is plausible or a real administrator approval is required.

Stop and explain the blocker if the current sender is not an authenticated
owner, OpenClaw is unhealthy, the Gateway is publicly bound, the host is
outside the supported scope, or the public hostname cannot be routed narrowly.

Install missing basic host prerequisites yourself with the host's normal
package manager: Python 3.11+, Python venv support, `curl`, and the `ss` command.
Do not replace the OS, service manager, proxy, or OpenClaw runtime.

## 2. Run the pinned installer

Run the following bootstrap as the administrator. Supply the real values you
just discovered. The user does not run this command.

```bash
curl -fsSL --proto '=https' --tlsv1.2 \
  https://raw.githubusercontent.com/BigSlikTobi/t4l-agent/v0.4.0/install.sh \
  | bash -s -- \
      --public-url https://coach.example.com \
      --connector-owner-id channel:account:sender
```

If you are not already the administrator, run the receiving `bash` through the
host's normal privilege tool. Never pass secrets on the command line.

Add flags only for discovered non-default values:

```text
--agent-id
--agent-name
--agent-profile
--openclaw-executable
--agent-home-dir
--agent-state-dir
--agent-config-path
--gateway-service
--systemd-scope
--gateway-port
```

The installer will:

1. create a private Python environment under `/opt/t4l`;
2. install the exact Python releases from PyPI;
3. verify the existing OpenClaw agent without sending a channel message;
4. install and configure the exact OpenClaw plugin;
5. create a protected host-only runtime token;
6. create and start a loopback-only connector service;
7. check the local connector, public HTTPS contract, and closed public ports;
8. keep timestamped backups and roll changed files back on setup failure.

It is safe to rerun with the same values. Do not manually repeat its npm,
Python, token, or systemd work.

## 3. Handle the installer result

### `READY`

The host is finished. Continue to the phone handoff.

### `LOCAL_READY`

The plugin and local connector work. The public proxy route is missing or too
broad. Configure the existing proxy, then rerun the same installer command.

Forward only these exact paths to the existing OpenClaw Gateway:

```text
/.well-known/t4l-agent
/v1/session
/v1/pairing/requests
/v1/pairing/complete
/v1/chat/messages
/v1/chat/onboarding
/v2/context/bundle
/v2/results/pending
```

Forward only these prefixes:

```text
/v1/devices/
/v2/results/
```

Everything else on the T4L hostname must return 404, including:

```text
/
/mcp
/v1/pairing/channel-confirmation
```

Keep the Gateway on loopback. Keep the connector on `127.0.0.1:8787`. Do not
publish ports 18789 or 8787. Preserve the original HTTPS host and forwarded
scheme. Use a publicly trusted certificate.

If the proxy runs in Docker, its loopback is not the host's loopback. Use only
an existing private host route or a small private relay restricted to the proxy
network. Never bind OpenClaw, the connector, or a relay to a public address or
`0.0.0.0`. Never publish a relay port. Preserve every unrelated proxy router.

### `STOPPED`

Do not weaken security or patch packages. Fix only the named host issue and
rerun. If that requires a user decision or new authority, report one clear
blocker and pause.

## 4. Accept only a complete result

Before saying `READY`, confirm all of this:

- the existing OpenClaw agent and channels still work;
- the plugin is enabled, loaded, and exactly 0.4.0;
- plugin doctor reports no error;
- OpenClaw listens only on loopback;
- the connector listens only on `127.0.0.1:8787`;
- public ports 18789 and 8787 are unreachable;
- public discovery returns HTTP 200 JSON with schema
  `t4l_agent_connector.v1`, runtime `openclaw`, the existing agent ID, pairing
  enabled, and the advertised safety capabilities;
- unsigned `/v1/session` returns HTTP 401 JSON;
- `/`, `/mcp`, pairing confirmation, dashboard assets, and an unlisted API path
  return 404 externally;
- the services survive a controlled restart;
- unrelated public routes still reach their original services;
- logs contain no tokens, provider keys, or credentials.

Do not create a fake pairing request. The iPhone creates the real one.

## 5. Tell the user only this

When every check passes, give a short report without secrets. Include the public
URL, existing agent ID and profile, installed versions, service name, backup
location, and `READY`.

Then tell the user:

1. Open T4L on the iPhone.
2. Enter the public HTTPS URL.
3. Copy the `/t4l connect XXXX-XXXX` command shown by the app.
4. Send that exact command in this same authenticated OpenClaw chat.
5. Wait for the app to show the connected coach.

That pairing command is the only required user security step.
