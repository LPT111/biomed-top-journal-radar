#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."
if [ -d .venv ]; then
  . .venv/bin/activate
fi

if [ -z "${SMTP_USER:-}" ]; then
  echo "需要设置 SMTP_USER=lipengtao12@gmail.com"
fi
if [ -z "${SMTP_APP_PASSWORD:-}" ]; then
  echo "需要设置 SMTP_APP_PASSWORD=你的 Gmail 应用专用密码"
fi
if [ -z "${EMAIL_TO:-}" ]; then
  echo "可设置 EMAIL_TO=lipengtao12@gmail.com"
fi

python run_daily.py --email-test
