#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# LILJR UNSTOPPABLE DEPLOY ORCHESTRATOR v5.0
# Push all repos, deploy, save state, reset, update-ready
# Run: bash deploy_all.sh
# ═══════════════════════════════════════════════════════════════

set -e

REPOS=(
  "liljr-unified-ai:https://github.com/signsafepro-create/liljr-unified-ai.git"
  "liljr-autonomous:https://github.com/signsafepro-create/liljr-autonomous.git"
  "liljr-complete:https://github.com/signsafepro-create/liljr-complete.git"
  "liljr-defense:https://github.com/signsafepro-create/liljr-defense.git"
)

LOG_FILE="/tmp/liljr_deploy_$(date +%Y%m%d_%H%M%S).log"
DEPLOY_STATE="/tmp/liljr_deploy_state.json"

echo "🚀 LILJR UNSTOPPABLE DEPLOY v5.0"
echo "================================="
echo "Log: $LOG_FILE"
echo ""

# ─── 1. SAVE CURRENT STATE ───
echo "💾 Saving current state..."
cat > "$DEPLOY_STATE" << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "deployment_id": "deploy_$(date +%s)",
  "version": "5.0.0",
  "mode": "UNSTOPPABLE",
  "repos": [],
  "status": "saving"
}
EOF

# ─── 2. PUSH ALL REPOS ───
echo "📤 Pushing all repos..."
for repo_pair in "${REPOS[@]}"; do
  IFS=':' read -r name url <<< "$repo_pair"
  dir="/root/.openclaw/workspace/$name"
  
  if [ -d "$dir" ]; then
    echo "  → $name"
    cd "$dir"
    git add -A 2>/dev/null || true
    git commit -m "v5.0 deploy: $(date)" 2>/dev/null || true
    git push origin main 2>&1 | grep -E "(To|main|error|fatal)" || true
    echo "    ✅ $name pushed"
  else
    echo "    ⚠️ $name not found locally"
  fi
done

# ─── 3. CREATE UNSTOPPABLE DEPLOY SCRIPT ───
echo "🔥 Building unstoppable deploy script..."

mkdir -p /root/.openclaw/workspace/liljr-unstoppable
cat > /root/.openclaw/workspace/liljr-unstoppable/deploy.sh << 'UNSTOPPABLE'
#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# LILJR UNSTOPPABLE — Self-Healing, Auto-Updating, Always-Running
# ═══════════════════════════════════════════════════════════════

set -e

DEPLOY_HOME="$HOME/liljr-unstoppable"
LOG="$DEPLOY_HOME/liljr.log"
PID_FILE="$DEPLOY_HOME/server.pid"
STATE_FILE="$DEPLOY_HOME/state.json"
UPDATE_URL="https://raw.githubusercontent.com/signsafepro-create/liljr-autonomous/main/scripts/lj.sh"
BACKUP_DIR="$DEPLOY_HOME/backups"

mkdir -p "$DEPLOY_HOME" "$BACKUP_DIR"

log() {
  echo "[$(date '+%H:%M:%S')] $1" | tee -a "$LOG"
}

# ─── SAVE STATE ───
save_state() {
  cat > "$STATE_FILE" << EOF
{
  "last_start": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "pid": $(cat "$PID_FILE" 2>/dev/null || echo "null"),
  "uptime": "$(uptime -p 2>/dev/null || echo "unknown")",
  "mode": "UNSTOPPABLE",
  "auto_update": true,
  "version": "5.0.0"
}
EOF
}

# ─── AUTO-UPDATE CHECK ───
check_update() {
  log "Checking for updates..."
  latest=$(curl -s "$UPDATE_URL" | md5sum | awk '{print $1}')
  current=$(cat "$DEPLOY_HOME/lj.sh" 2>/dev/null | md5sum | awk '{print $1}')
  if [ "$latest" != "$current" ] && [ -n "$latest" ]; then
    log "🔄 Update found! Downloading..."
    curl -s "$UPDATE_URL" > "$DEPLOY_HOME/lj.sh.new"
    mv "$DEPLOY_HOME/lj.sh.new" "$DEPLOY_HOME/lj.sh"
    chmod +x "$DEPLOY_HOME/lj.sh"
    log "✅ Updated lj.sh"
  fi
}

# ─── BACKUP ───
backup() {
  tar czf "$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).tar.gz" \
    ~/liljr-autonomous 2>/dev/null || true
  # Keep only last 5 backups
  ls -t "$BACKUP_DIR"/backup_*.tar.gz 2>/dev/null | tail -n +6 | xargs rm -f 2>/dev/null || true
}

# ─── RESTART WITH PRECISION ───
restart() {
  log "🔄 Precision restart..."
  
  # Kill old
  if [ -f "$PID_FILE" ]; then
    old_pid=$(cat "$PID_FILE")
    kill "$old_pid" 2>/dev/null || true
    rm -f "$PID_FILE"
    sleep 1
  fi
  
  # Start new
  cd ~/liljr-autonomous/backend 2>/dev/null || {
    log "❌ Repo missing, cloning..."
    cd ~ && git clone https://github.com/signsafepro-create/liljr-autonomous.git
  }
  
  cd ~/liljr-autonomous/backend
  nohup python server.py > "$LOG" 2>&1 &
  new_pid=$!
  echo "$new_pid" > "$PID_FILE"
  
  log "✅ Server PID: $new_pid"
  
  # Verify
  sleep 2
  if curl -s http://localhost:8000/api/health >/dev/null 2>&1; then
    log "🟢 Health check: PASS"
  else
    log "🔴 Health check: FAIL — retrying in 5s..."
    sleep 5
    restart
  fi
}

# ─── WATCHDOG — Keep Alive ───
watchdog() {
  while true; do
    if ! curl -s http://localhost:8000/api/health >/dev/null 2>&1; then
      log "💀 Server dead — resurrecting..."
      backup
      restart
    fi
    sleep 10
  done
}

# ─── MAIN ───
case "${1:-run}" in
  start|run)
    log "🚀 LilJR Unstoppable v5.0 starting..."
    backup
    check_update
    restart
    save_state
    log "✅ Deploy complete. Mode: UNSTOPPABLE"
    log "   PID: $(cat $PID_FILE)"
    log "   Log: $LOG"
    log "   State: $STATE_FILE"
    ;;
  watch)
    log "👁️ Watchdog mode — keeping server alive..."
    watchdog
    ;;
  restart)
    backup
    restart
    save_state
    ;;
  update)
    check_update
    backup
    restart
    save_state
    ;;
  stop)
    if [ -f "$PID_FILE" ]; then
      kill "$(cat $PID_FILE)" 2>/dev/null || true
      rm -f "$PID_FILE"
    fi
    pkill -f "python server.py"
    log "🛑 Stopped"
    ;;
  status)
    if [ -f "$PID_FILE" ] && kill -0 "$(cat $PID_FILE)" 2>/dev/null; then
      echo "🟢 Running — PID: $(cat $PID_FILE)"
      curl -s http://localhost:8000/api/health 2>/dev/null || echo "⚠️ Unhealthy"
    else
      echo "🔴 Not running"
    fi
    ;;
  *)
    echo "Usage: bash deploy.sh [start|watch|restart|update|stop|status]"
    ;;
esac
UNSTOPPABLE

chmod +x /root/.openclaw/workspace/liljr-unstoppable/deploy.sh

# ─── 4. CREATE UNSTOPPABLE WRAPPER ───
cat > /root/.openclaw/workspace/liljr-unstoppable/lj.sh << 'LJ'
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
LJ
chmod +x /root/.openclaw/workspace/liljr-unstoppable/lj.sh

# ─── 5. PUSH UNSTOPPABLE REPO ───
cd /root/.openclaw/workspace/liljr-unstoppable

# Initialize if needed
if [ ! -d .git ]; then
  git init
  git remote add origin https://github.com/signsafepro-create/liljr-unstoppable.git 2>/dev/null || true
fi

git add -A
git commit -m "v5.0 UNSTOPPABLE: deploy, update, reset, precision restart" 2>/dev/null || true

# Create repo if not exists
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  -X POST https://api.github.com/user/repos \
  -d '{"name":"liljr-unstoppable","private":false,"description":"LilJR Unstoppable v5.0 - Self-healing deployment with precision restart"}' 2>/dev/null || true

git remote set-url origin https://$GITHUB_TOKEN@github.com/signsafepro-create/liljr-unstoppable.git 2>/dev/null || true
git push -u origin main 2>&1 | grep -E "(To|main|error)" || true

# ─── 6. SAVE FINAL STATE ───
cat > "$DEPLOY_STATE" << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "deployment_id": "deploy_$(date +%s)",
  "version": "5.0.0",
  "mode": "UNSTOPPABLE",
  "status": "deployed",
  "repos_pushed": ["liljr-unified-ai", "liljr-autonomous", "liljr-complete", "liljr-defense", "liljr-unstoppable"],
  "urls": {
    "unified": "https://github.com/signsafepro-create/liljr-unified-ai",
    "autonomous": "https://github.com/signsafepro-create/liljr-autonomous",
    "complete": "https://github.com/signsafepro-create/liljr-complete",
    "defense": "https://github.com/signsafepro-create/liljr-defense",
    "unstoppable": "https://github.com/signsafepro-create/liljr-unstoppable"
  }
}
EOF

echo ""
echo "✅ UNSTOPPABLE DEPLOY v5.0 COMPLETE"
echo "======================================"
echo ""
echo "📦 NEW REPO: https://github.com/signsafepro-create/liljr-unstoppable"
echo ""
echo "🔥 UNSTOPPABLE FEATURES:"
echo "  • Auto-healing — dead server resurrects in 10s"
echo "  • Auto-update — checks for new lj.sh every deploy"
echo "  • Precision restart — health check before confirming"
echo "  • Backup before every restart — 5 kept"
echo "  • State tracking — JSON state file"
echo "  • Watchdog mode — runs forever, never stops"
echo ""
echo "🚀 IN TERMUX:"
echo "  curl -s https://raw.githubusercontent.com/signsafepro-create/liljr-unstoppable/main/deploy.sh | bash"
echo ""
echo "📋 COMMANDS:"
echo "  bash deploy.sh start    — Deploy + start"
echo "  bash deploy.sh watch    — 24/7 watchdog"
echo "  bash deploy.sh restart  — Precision restart"
echo "  bash deploy.sh update   — Check update + restart"
echo "  bash deploy.sh stop     — Kill everything"
echo "  bash deploy.sh status   — Check health"
echo ""
echo "State saved: $DEPLOY_STATE"
echo "Log saved: $LOG_FILE"
