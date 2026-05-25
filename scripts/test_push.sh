#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."
if [ -d .venv ]; then
  . .venv/bin/activate
fi

if [ -z "${FEISHU_WEBHOOK_URL:-}" ] && [ -z "${WECOM_WEBHOOK_URL:-}" ] && [ -z "${WECHAT_WEBHOOK_URL:-}" ]; then
  echo "未检测到推送 webhook。可执行："
  echo "export FEISHU_WEBHOOK_URL='你的 lpt 的智能助手/龙虾 webhook'"
  echo "或 export WECOM_WEBHOOK_URL='你的企业微信机器人 webhook'"
  exit 0
fi

python run_daily.py --push-test
