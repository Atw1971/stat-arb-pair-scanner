#!/bin/zsh

set -euo pipefail

MACMINI_USER="waratat"
MACMINI_HOST="192.168.1.35"
KEY_PATH="$HOME/.ssh/id_ed25519_github_codex"
PUB_KEY_PATH="${KEY_PATH}.pub"

if [[ ! -f "$PUB_KEY_PATH" ]]; then
  echo "ไม่พบ SSH public key: $PUB_KEY_PATH"
  exit 1
fi

echo "กำลังใส่ SSH key เข้า Mac mini: ${MACMINI_USER}@${MACMINI_HOST}"
echo "ถ้าถาม password ให้ใส่ password ของ Mac mini"

cat "$PUB_KEY_PATH" | ssh -o StrictHostKeyChecking=accept-new "${MACMINI_USER}@${MACMINI_HOST}" '
  set -e
  mkdir -p ~/.ssh
  chmod 700 ~/.ssh
  touch ~/.ssh/authorized_keys
  chmod 600 ~/.ssh/authorized_keys
  key="$(cat)"
  if ! grep -qxF "$key" ~/.ssh/authorized_keys; then
    printf "%s\n" "$key" >> ~/.ssh/authorized_keys
  fi
  echo "SSH key พร้อมแล้วบน Mac mini"
'

echo
echo "ทดสอบ SSH..."
ssh -i "$KEY_PATH" "${MACMINI_USER}@${MACMINI_HOST}" 'hostname && whoami'
echo
echo "เรียบร้อย: เครื่องนี้เข้า Mac mini ด้วย SSH key ได้แล้ว"
