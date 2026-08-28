#!/usr/bin/env bash
# PreToolUse (Bash) hook: deny any command that references a .env secrets file.
#
# Reads the hook payload from stdin, extracts .tool_input.command, and blocks the
# call when the command mentions a `.env` file. `.env.example` / `.env.sample` /
# `.env.template` / `.env.dist` are allowed (they carry no secrets).
#
# On a block: prints a PreToolUse JSON decision with permissionDecision=deny and
# exits 0 (the JSON, not the exit code, carries the verdict). Otherwise exits 0
# silently and the Bash call proceeds untouched.
set -euo pipefail

payload="$(cat)"

command="$(printf '%s' "$payload" | jq -r '.tool_input.command // ""')"

# Drop the allowed non-secret variants before testing for a bare `.env` token.
stripped="$command"
for allowed in .env.example .env.sample .env.template .env.dist; do
  stripped="${stripped//$allowed/}"
done

# Match `.env` as a whole filename token: `.env`, `.env.local`, `.env.production`,
# `config/.env`, `xxd .env |` — but not `.environment`, `.envrc`, `--env`.
if printf '%s' "$stripped" | grep -Eq '\.env(\.[A-Za-z0-9_-]+)?([^A-Za-z0-9_.-]|$)'; then
  reason='Bloqueado: el comando referencia un archivo .env (secretos). Estos archivos no se leen por Bash. Usa .env.example o pide el valor puntual al usuario.'
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":%s}}\n' \
    "$(printf '%s' "$reason" | jq -Rs .)"
  exit 0
fi

exit 0
