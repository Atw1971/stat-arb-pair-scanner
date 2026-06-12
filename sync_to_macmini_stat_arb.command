#!/bin/zsh

set -euo pipefail

MACMINI_USER="waratat"
MACMINI_HOST="192.168.1.35"
KEY_PATH="$HOME/.ssh/id_ed25519_github_codex"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
REMOTE_DIR="Documents/stat-arb-pair-scanner"

echo "กำลัง sync โปรเจกต์จากเครื่องนี้ไป Mac mini: ${MACMINI_USER}@${MACMINI_HOST}"
echo "ปลายทาง: ~/${REMOTE_DIR}"

ssh -i "$KEY_PATH" -o StrictHostKeyChecking=accept-new "${MACMINI_USER}@${MACMINI_HOST}" "mkdir -p ~/${REMOTE_DIR}"

rsync -az --delete \
  --exclude ".git/" \
  --exclude ".venv/" \
  --exclude "__pycache__/" \
  --exclude "*.pyc" \
  --exclude ".DS_Store" \
  "$PROJECT_DIR/" \
  "${MACMINI_USER}@${MACMINI_HOST}:~/${REMOTE_DIR}/"

ssh -i "$KEY_PATH" "${MACMINI_USER}@${MACMINI_HOST}" "
  set -e
  cd ~/${REMOTE_DIR}
  chmod +x install_desktop_app.command start_stat_arb_pair_scanner.command
  ./install_desktop_app.command
"

echo
echo "เรียบร้อย: Mac mini ได้ไฟล์ล่าสุดจากเครื่องนี้แล้ว"
