#!/bin/zsh

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
DESKTOP_DIR="$HOME/Desktop"
APP_NAME="Stat Arb Pair Scanner.app"
COMMAND_NAME="Stat Arb Pair Scanner.command"

chmod +x "$PROJECT_DIR/start_stat_arb_pair_scanner.command"

rm -rf "$DESKTOP_DIR/$APP_NAME"
cp -R "$PROJECT_DIR/$APP_NAME" "$DESKTOP_DIR/$APP_NAME"
chmod +x "$DESKTOP_DIR/$APP_NAME/Contents/MacOS/launcher"
mkdir -p "$DESKTOP_DIR/$APP_NAME/Contents/Resources"
printf '%s\n' "$PROJECT_DIR" > "$DESKTOP_DIR/$APP_NAME/Contents/Resources/project_path.txt"

cp "$PROJECT_DIR/start_stat_arb_pair_scanner.command" "$DESKTOP_DIR/$COMMAND_NAME"
chmod +x "$DESKTOP_DIR/$COMMAND_NAME"

xattr -dr com.apple.quarantine "$DESKTOP_DIR/$APP_NAME" 2>/dev/null || true
xattr -d com.apple.quarantine "$DESKTOP_DIR/$COMMAND_NAME" 2>/dev/null || true

echo "Installed $DESKTOP_DIR/$APP_NAME"
echo "Installed $DESKTOP_DIR/$COMMAND_NAME"
