#!/bin/zsh

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

cd "$PROJECT_DIR"

echo "กำลังเตรียมอัปเดต GitHub..."
echo "Project: $PROJECT_DIR"
echo

git add app.py setup_macmini_ssh.command sync_to_macmini_stat_arb.command update_macmini_stat_arb.command push_to_github.command

if git diff --cached --quiet; then
  echo "ไม่มีไฟล์ใหม่ที่ต้อง commit"
else
  git commit -m "Add symbol validation to scanner app"
fi

echo
echo "กำลังดึงของล่าสุดจาก GitHub..."
git pull --rebase origin main

echo
echo "กำลัง push ขึ้น GitHub..."
git push origin main

echo
echo "เรียบร้อย: GitHub อัปเดตแล้ว"
