#!/bin/zsh

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
DESKTOP_DIR="$HOME/Desktop"
APP_PATH="$DESKTOP_DIR/Stat Arb Pair Scanner.app"
COMMAND_PATH="$DESKTOP_DIR/Stat Arb Pair Scanner.command"
HINT_FILE="$APP_PATH/Contents/Resources/project_path.txt"
PORT="8510"

echo "Project path ที่ถูกต้อง:"
echo "$PROJECT_DIR"
echo

if [[ -d "$APP_PATH" ]]; then
  mkdir -p "$APP_PATH/Contents/Resources"
  printf "%s\n" "$PROJECT_DIR" > "$HINT_FILE"
  chmod +x "$APP_PATH/Contents/MacOS/launcher" 2>/dev/null || true
  echo "แก้ project_path.txt แล้ว: $HINT_FILE"
else
  echo "ยังไม่พบ Desktop app จะติดตั้งใหม่"
  "$PROJECT_DIR/install_desktop_app.command"
fi

cat >"$COMMAND_PATH" <<EOF
#!/bin/zsh
set -euo pipefail
cd "$PROJECT_DIR"
exec ./start_stat_arb_pair_scanner.command
EOF
chmod +x "$COMMAND_PATH"
echo "แก้ command launcher แล้ว: $COMMAND_PATH"

echo
echo "ปิด server เก่าที่ port $PORT..."
pids="$(lsof -tiTCP:"$PORT" -sTCP:LISTEN 2>/dev/null || true)"
if [[ -n "$pids" ]]; then
  kill $pids >/dev/null 2>&1 || true
  sleep 1
fi
pids="$(lsof -tiTCP:"$PORT" -sTCP:LISTEN 2>/dev/null || true)"
if [[ -n "$pids" ]]; then
  kill -9 $pids >/dev/null 2>&1 || true
  sleep 1
fi

echo "เปิดแอปใหม่..."
cd "$PROJECT_DIR"
exec ./start_stat_arb_pair_scanner.command
