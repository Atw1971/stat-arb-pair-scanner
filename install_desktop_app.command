#!/bin/zsh

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
DESKTOP_DIR="$HOME/Desktop"
APP_NAME="Stat Arb Pair Scanner.app"
COMMAND_NAME="Stat Arb Pair Scanner.command"
LEGACY_COMMAND_NAME="Open Stat Arb Pair Scanner.command"
PROJECT_HINT_FILE="$DESKTOP_DIR/$APP_NAME/Contents/Resources/project_path.txt"
COMMAND_TARGET="$DESKTOP_DIR/$COMMAND_NAME"

chmod +x "$PROJECT_DIR/start_stat_arb_pair_scanner.command"

rm -f "$DESKTOP_DIR/$LEGACY_COMMAND_NAME"
rm -rf "$DESKTOP_DIR/$APP_NAME"
cp -R "$PROJECT_DIR/$APP_NAME" "$DESKTOP_DIR/$APP_NAME"
chmod +x "$DESKTOP_DIR/$APP_NAME/Contents/MacOS/launcher"
mkdir -p "$DESKTOP_DIR/$APP_NAME/Contents/Resources"
printf '%s\n' "$PROJECT_DIR" > "$PROJECT_HINT_FILE"

cat >"$COMMAND_TARGET" <<EOF
#!/bin/zsh

set -euo pipefail

PROJECT_DIR="$(cat "$PROJECT_HINT_FILE" 2>/dev/null || true)"

if [[ -z "\$PROJECT_DIR" || ! -f "\$PROJECT_DIR/start_stat_arb_pair_scanner.command" ]]; then
  for candidate in \
    "$PROJECT_DIR" \
    "\$HOME/Documents/stat-arb-pair-scanner" \
    "\$HOME/Documents/Codex/2026-05-26/new-chat" \
    "\$HOME/Documents/GitHub/stat-arb-pair-scanner"
  do
    if [[ -f "\$candidate/start_stat_arb_pair_scanner.command" ]]; then
      PROJECT_DIR="\$candidate"
      break
    fi
  done
fi

if [[ -z "\$PROJECT_DIR" || ! -f "\$PROJECT_DIR/start_stat_arb_pair_scanner.command" ]]; then
  /usr/bin/osascript -e 'display alert "Stat Arb Pair Scanner" message "หาโฟลเดอร์โปรเจกต์ไม่เจอ กรุณา clone repo ชื่อ stat-arb-pair-scanner แล้วรัน install_desktop_app.command ก่อน"' >/dev/null 2>&1 || true
  exit 1
fi

cd "\$PROJECT_DIR"
exec ./start_stat_arb_pair_scanner.command
EOF
chmod +x "$COMMAND_TARGET"

xattr -dr com.apple.quarantine "$DESKTOP_DIR/$APP_NAME" 2>/dev/null || true
xattr -d com.apple.quarantine "$COMMAND_TARGET" 2>/dev/null || true

echo "Installed $DESKTOP_DIR/$APP_NAME"
echo "Installed $COMMAND_TARGET"
echo "Project hint written to $PROJECT_HINT_FILE"
