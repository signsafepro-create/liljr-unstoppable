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
