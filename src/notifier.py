from __future__ import annotations

import os
from typing import Any

import requests


def _message(items: list[dict[str, Any]], dashboard_url: str) -> str:
    lines = [
        "全医学顶刊与 RCT 雷达已更新",
        f"今日筛选文献数量：{len(items)}",
    ]
    if dashboard_url:
        lines.append(f"网页版：{dashboard_url}")
    lines.append("")
    lines.append("Top 5：")
    for i, item in enumerate(items[:5], 1):
        lines.append(f"{i}. {item.get('title','')}")
        lines.append(f"   {item.get('journal','')}｜{item.get('study_type','')}｜Score {item.get('score','')}")
    lines.append("")
    lines.append("回复/追问可让龙虾继续写推文、筛重点、补充背景。")
    return "\n".join(lines)


def send_push(items: list[dict[str, Any]], generated_at: str = "") -> bool:
    dashboard_url = os.getenv("PUBLIC_DASHBOARD_URL", "")
    text = _message(items, dashboard_url)
    feishu = os.getenv("FEISHU_WEBHOOK_URL")
    wecom = os.getenv("WECOM_WEBHOOK_URL")
    generic_wechat = os.getenv("WECHAT_WEBHOOK_URL")

    sent = False
    if feishu:
        try:
            payload = {
                "msg_type": "interactive",
                "card": {
                    "config": {"wide_screen_mode": True},
                    "header": {"title": {"tag": "plain_text", "content": "全医学顶刊与 RCT 雷达已更新"}, "template": "turquoise"},
                    "elements": [
                        {"tag": "div", "text": {"tag": "lark_md", "content": text.replace("\n", "\n\n")}},
                    ],
                },
            }
            resp = requests.post(feishu, json=payload, timeout=20)
            if resp.status_code >= 300:
                print(f"Feishu push failed: {resp.status_code} {resp.text[:500]}")
            else:
                print("Feishu push sent.")
                sent = True
        except Exception as exc:
            print(f"Feishu push failed: {exc!r}")

    for name, url in [("WeCom", wecom), ("WeChat", generic_wechat)]:
        if not url:
            continue
        try:
            resp = requests.post(url, json={"msgtype": "text", "text": {"content": text}}, timeout=20)
            if resp.status_code >= 300:
                print(f"{name} push failed: {resp.status_code} {resp.text[:500]}")
            else:
                print(f"{name} push sent.")
                sent = True
        except Exception as exc:
            print(f"{name} push failed: {exc!r}")

    if not sent and not any([feishu, wecom, generic_wechat]):
        print("Push skipped because webhook is missing.")
    return sent
