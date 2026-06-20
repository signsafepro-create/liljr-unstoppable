#!/bin/bash
# Unstoppable wrapper — always works, auto-heals

DEPLOY_HOME="$HOME/liljr-unstoppable"

# If server not running, start it
if ! curl -s http://localhost:8000/api/health >/dev/null 2>&1; then
  bash "$DEPLOY_HOME/deploy.sh" start >/dev/null 2>&1 &
  sleep 3
fi

# Pass through to actual lj
bash ~/lj "$@" 2>/dev/null || {
  # Fallback if ~/lj missing
  curl -s "https://raw.githubusercontent.com/signsafepro-create/liljr-autonomous/main/scripts/lj.sh" > /tmp/lj_fallback
  bash /tmp/lj_fallback "$@"
}
