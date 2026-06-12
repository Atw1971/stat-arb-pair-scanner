#!/bin/zsh

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PORT="8510"
HOST="127.0.0.1"
APP_URL="http://${HOST}:${PORT}/?v=$(date +%s)"
HEALTH_URL="http://${HOST}:${PORT}/_stcore/health"
LOG_FILE="/tmp/stat-arb-pair-scanner.log"
VENV_DIR="$PROJECT_DIR/.venv"
PYTHON_BIN="$VENV_DIR/bin/python"
PIP_BIN="$VENV_DIR/bin/pip"
STREAMLIT_BIN="$VENV_DIR/bin/streamlit"

show_alert() {
  local message="$1"
  /usr/bin/osascript -e "display alert \"Stat Arb Pair Scanner\" message $(printf '%q' "$message")" >/dev/null 2>&1 || true
}

port_listening() {
  lsof -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1
}

ensure_environment() {
  if ! command -v python3 >/dev/null 2>&1; then
    show_alert "ไม่พบ python3 บนเครื่อง จึงยังเปิด Stat Arb Pair Scanner ไม่ได้"
    exit 1
  fi

  if [[ ! -x "$PYTHON_BIN" ]]; then
    python3 -m venv "$VENV_DIR"
  fi

  "$PYTHON_BIN" -m pip install --upgrade pip setuptools wheel >/tmp/stat-arb-pair-scanner-bootstrap.log 2>&1
  "$PIP_BIN" install -r "$PROJECT_DIR/requirements.txt" >/tmp/stat-arb-pair-scanner-install.log 2>&1
}

start_server() {
  osascript <<APPLESCRIPT
tell application "Terminal"
  activate
  do script "cd " & quoted form of "$PROJECT_DIR" & "; nohup " & quoted form of "$STREAMLIT_BIN" & " run app.py --server.port ${PORT} --server.address ${HOST} --server.fileWatcherType none --server.headless true --browser.gatherUsageStats false > " & quoted form of "$LOG_FILE" & " 2>&1 &"
end tell
APPLESCRIPT
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

if ! port_listening; then
  start_server
fi

if wait_for_health; then
  /usr/bin/open "$APP_URL"
  exit 0
fi

show_alert "เซิร์ฟเวอร์ยังไม่พร้อมภายในเวลาที่กำหนด ดู log ได้ที่ $LOG_FILE"
exit 1
