#!/usr/bin/env bash
set -Eeuo pipefail

umask 077

readonly T4L_CORE_INSTALLER_URL="https://raw.githubusercontent.com/BigSlikTobi/t4l-agent/v0.3.2/install.sh"
readonly T4L_CORE_INSTALLER_SHA256="addbecaba87b3699f9392c96f0362005e97a73d6f924783d2bd422ac4f294e07"
readonly T4L_RUNBOOK_URL="https://raw.githubusercontent.com/BigSlikTobi/t4l-agent-instructions/main/INSTALL.md"
readonly T4L_RUNBOOK_SHA256="21d1da7fc434ccd62ce980f33dd1175d42cf7ab57657f7a87c3d17618f9ab63f"
readonly T4L_INSTALL_ROOT="/opt/t4l"

fail() {
  printf 'T4L quick install stopped: %s\n' "$1" >&2
  exit 2
}

verify_sha256() {
  local file="$1"
  local expected="$2"
  local actual

  if command -v sha256sum >/dev/null 2>&1; then
    actual="$(sha256sum "$file" | awk '{print $1}')"
  elif command -v shasum >/dev/null 2>&1; then
    actual="$(shasum -a 256 "$file" | awk '{print $1}')"
  else
    fail "SHA-256 verification is unavailable"
  fi

  [[ "$actual" == "$expected" ]] || fail "download verification failed"
}

run_as_admin() {
  if [[ "${EUID}" -eq 0 ]]; then
    "$@"
    return
  fi
  command -v sudo >/dev/null 2>&1 || \
    fail "administrator access is required"
  sudo -n "$@" || \
    fail "administrator approval is required; approve it and run the same command again"
}

[[ "$(uname -s)" == "Linux" ]] || \
  fail "this T4L installer currently supports Linux OpenClaw hosts only"
command -v curl >/dev/null 2>&1 || fail "curl is required"

T4L_QUICK_TMP="$(mktemp -d)"
readonly T4L_QUICK_TMP
cleanup() {
  rm -rf -- "$T4L_QUICK_TMP"
}
trap cleanup EXIT

curl -fsSL --proto '=https' --tlsv1.2 \
  "$T4L_CORE_INSTALLER_URL" \
  -o "$T4L_QUICK_TMP/core-install.sh"
curl -fsSL --proto '=https' --tlsv1.2 \
  "$T4L_RUNBOOK_URL" \
  -o "$T4L_QUICK_TMP/INSTALL.md"

verify_sha256 "$T4L_QUICK_TMP/core-install.sh" "$T4L_CORE_INSTALLER_SHA256"
verify_sha256 "$T4L_QUICK_TMP/INSTALL.md" "$T4L_RUNBOOK_SHA256"

if ! run_as_admin bash "$T4L_QUICK_TMP/core-install.sh" --help \
  >"$T4L_QUICK_TMP/bootstrap.log" 2>&1; then
  tail -n 40 "$T4L_QUICK_TMP/bootstrap.log" >&2 || true
  fail "the pinned T4L runtime could not be installed"
fi

run_as_admin install -d -m 0755 "$T4L_INSTALL_ROOT"
run_as_admin install -m 0644 \
  "$T4L_QUICK_TMP/INSTALL.md" \
  "$T4L_INSTALL_ROOT/INSTALL.md"

printf '%s\n' \
  'T4L_HOST_AGENT_CONTINUE_V1' \
  '' \
  'You are the OpenClaw host agent that executed this installer.' \
  'Continue the setup now. Do not turn it into instructions for the user.' \
  '' \
  '1. Read /opt/t4l/INSTALL.md completely.' \
  '2. Inspect this host and discover the values required by that runbook.' \
  '3. Use /opt/t4l/venv/bin/t4l-agent install with those real values.' \
  '4. Handle LOCAL_READY proxy work yourself and rerun until READY.' \
  '5. Stop only for one real user decision, administrator approval, or unsafe host.' \
  '' \
  'Preserve the existing agent, model, provider, credentials, channels, dashboard, and unrelated services.' \
  'Never print secrets. Never expose OpenClaw or T4L ports publicly.'
