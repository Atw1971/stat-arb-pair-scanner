#!/bin/zsh

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPORTS_DIR="$PROJECT_DIR/reports"
PORT="8510"
HOST="127.0.0.1"
APP_URL="http://${HOST}:${PORT}/?v=$(date +%s)"
HEALTH_URL="http://${HOST}:${PORT}/_stcore/health"
LOG_FILE="$REPORTS_DIR/stat_arb_pair_scanner.log"
BOOTSTRAP_LOG="$REPORTS_DIR/stat_arb_pair_scanner_bootstrap.log"
INSTALL_LOG="$REPORTS_DIR/stat_arb_pair_scanner_install.log"
VENV_DIR="$PROJECT_DIR/.venv"
PYTHON_BIN="$VENV_DIR/bin/python"
PIP_BIN="$VENV_DIR/bin/pip"
STREAMLIT_BIN="$VENV_DIR/bin/streamlit"

mkdir -p "$REPORTS_DIR"

show_alert() {
  local message="$1"
  /usr/bin/osascript -e "display alert \"Stat Arb Pair Scanner\" message $(printf '%q' "$message")" >/dev/null 2>&1 || true
}

write_log() {
  local message="$1"
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$message" >>"$LOG_FILE"
}

port_listening() {
  lsof -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1
}

stop_existing_server() {
  local pids
  pids="$(lsof -tiTCP:"$PORT" -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -z "$pids" ]]; then
    return 0
  fi

  write_log "Stopping existing Streamlit server on port $PORT: $pids"
  kill $pids >/dev/null 2>&1 || true
  for _ in $(seq 1 10); do
    if ! port_listening; then
      return 0
    fi
    sleep 1
  done
  write_log "Existing server did not stop cleanly; force stopping: $pids"
  kill -9 $pids >/dev/null 2>&1 || true
  sleep 1
}

ensure_environment() {
  if ! command -v python3 >/dev/null 2>&1; then
    show_alert "ไม่พบ python3 บนเครื่อง จึงยังเปิด Stat Arb Pair Scanner ไม่ได้"
    exit 1
  fi

  if [[ ! -x "$PYTHON_BIN" ]]; then
    write_log "Creating virtual environment at $VENV_DIR"
    python3 -m venv "$VENV_DIR"
  fi

  if ! "$PYTHON_BIN" -m pip --version >/dev/null 2>&1; then
    write_log "Virtual environment is missing pip; rebuilding $VENV_DIR"
    rm -rf "$VENV_DIR"
    python3 -m venv "$VENV_DIR"
    "$PYTHON_BIN" -m ensurepip --upgrade >"$BOOTSTRAP_LOG" 2>&1 || true
  fi

  write_log "Installing and refreshing Python dependencies"
  "$PYTHON_BIN" -m pip install --upgrade pip setuptools wheel >"$BOOTSTRAP_LOG" 2>&1
  "$PIP_BIN" install -r "$PROJECT_DIR/requirements.txt" >"$INSTALL_LOG" 2>&1
}

start_server() {
  write_log "Starting Streamlit server on $HOST:$PORT"
  cd "$PROJECT_DIR"
  nohup "$STREAMLIT_BIN" run app.py \
    --server.port "$PORT" \
    --server.address "$HOST" \
    --server.fileWatcherType none \
    --server.headless true \
    --browser.gatherUsageStats false \
    >"$LOG_FILE" 2>&1 &
}

wait_for_health() {
  for _ in $(seq 1 30); do
    if /usr/bin/curl -sf "$HEALTH_URL" | /usr/bin/grep -qi "ok"; then
      return 0
    fi
    sleep 1
  done
  return 1
}

cd "$PROJECT_DIR"
ensure_environment

stop_existing_server

start_server

if wait_for_health; then
  write_log "Health check passed; opening browser"
  /usr/bin/open "$APP_URL"
  exit 0
fi

write_log "Server did not become healthy in time"
show_alert "เซิร์ฟเวอร์ยังไม่พร้อมภายในเวลาที่กำหนด ดู log ได้ที่ $LOG_FILE"
exit 1
