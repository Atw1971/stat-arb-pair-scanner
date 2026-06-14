#!/bin/zsh

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PORT="8510"

echo "กำลังปิด Stat Arb server เก่าที่ port ${PORT}..."
pids="$(lsof -tiTCP:"$PORT" -sTCP:LISTEN 2>/dev/null || true)"
if [[ -n "$pids" ]]; then
  echo "พบ process: $pids"
  kill $pids >/dev/null 2>&1 || true
  sleep 1
fi

pids="$(lsof -tiTCP:"$PORT" -sTCP:LISTEN 2>/dev/null || true)"
if [[ -n "$pids" ]]; then
  echo "ยังไม่หยุด ใช้ force kill: $pids"
  kill -9 $pids >/dev/null 2>&1 || true
  sleep 1
fi

echo "เปิด Stat Arb Pair Scanner ใหม่..."
cd "$PROJECT_DIR"
exec ./start_stat_arb_pair_scanner.command
