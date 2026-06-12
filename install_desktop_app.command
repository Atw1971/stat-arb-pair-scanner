#!/bin/zsh

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
DESKTOP_DIR="$HOME/Desktop"
APP_NAME="Stat Arb Pair Scanner.app"
COMMAND_NAME="Stat Arb Pair Scanner.command"
LEGACY_COMMAND_NAME="Open Stat Arb Pair Scanner.command"
PROJECT_HINT_FILE="$DESKTOP_DIR/$APP_NAME/Contents/Resources/project_path.txt"

chmod +x "$PROJECT_DIR/start_stat_arb_pair_scanner.command"

rm -f "$DESKTOP_DIR/$LEGACY_COMMAND_NAME"
rm -rf "$DESKTOP_DIR/$APP_NAME"
cp -R "$PROJECT_DIR/$APP_NAME" "$DESKTOP_DIR/$APP_NAME"
chmod +x "$DESKTOP_DIR/$APP_NAME/Contents/MacOS/launcher"
mkdir -p "$DESKTOP_DIR/$APP_NAME/Contents/Resources"
printf '%s\n' "$PROJECT_DIR" > "$PROJECT_HINT_FILE"

cp "$PROJECT_DIR/start_stat_arb_pair_scanner.command" "$DESKTOP_DIR/$COMMAND_NAME"
chmod +x "$DESKTOP_DIR/$COMMAND_NAME"

xattr -dr com.apple.quarantine "$DESKTOP_DIR/$APP_NAME" 2>/dev/null || true
xattr -d com.apple.quarantine "$DESKTOP_DIR/$COMMAND_NAME" 2>/dev/null || true

echo "Installed $DESKTOP_DIR/$APP_NAME"
echo "Installed $DESKTOP_DIR/$COMMAND_NAME"
echo "Project hint written to $PROJECT_HINT_FILE"
