#!/bin/zsh

set -euo pipefail

MACMINI_USER="waratat"
MACMINI_HOST="192.168.1.35"
KEY_PATH="$HOME/.ssh/id_ed25519"
REPO_SSH="git@github.com:Atw1971/stat-arb-pair-scanner.git"
REPO_DIR="\$HOME/Documents/stat-arb-pair-scanner"

echo "กำลังอัปเดต Stat Arb Pair Scanner บน Mac mini: ${MACMINI_USER}@${MACMINI_HOST}"

ssh -i "$KEY_PATH" -o StrictHostKeyChecking=accept-new "${MACMINI_USER}@${MACMINI_HOST}" "
  set -e
  if [[ -d \"\$HOME/Documents/stat-arb-pair-scanner/.git\" ]]; then
    cd \"\$HOME/Documents/stat-arb-pair-scanner\"
    git pull
  else
    mkdir -p \"\$HOME/Documents\"
    cd \"\$HOME/Documents\"
    git clone \"$REPO_SSH\" stat-arb-pair-scanner
    cd stat-arb-pair-scanner
  fi

  chmod +x install_desktop_app.command start_stat_arb_pair_scanner.command
  ./install_desktop_app.command
"

echo
echo "เรียบร้อย: Mac mini pull/install แอปล่าสุดแล้ว"
