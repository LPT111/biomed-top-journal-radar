from __future__ import annotations

import os
from typing import Any

import requests


def _message(items: list[dict[str, Any]], dashboard_url: str) -> str:
    cn_items = [x for x in items if x.get("content_bucket") == "cn_news"][:5]
    intl_items = [x for x in items if x.get("content_bucket") == "intl_news"][:15]
    top3 = sorted(items, key=lambda x: x.get("score", 0), reverse=True)[:3]
    def title(item: dict[str, Any]) -> str:
        return item.get("translated_title_cn") or item.get("tweet_title_cn") or item.get("title", "")
    lines = [
        "【Biomed Radar】今日医学科学新闻已更新",
        "",
        f"今日 {len(items)} 条：",
        f"中文来源 {sum(1 for x in items if x.get('source_region') == 'cn')} 条｜国际来源 {sum(1 for x in items if x.get('source_region') == 'intl')} 条",
        "",
        "今日头条：",
    ]
    for i, item in enumerate(top3, 1):
        lines.append(f"{i}. {title(item)}｜{item.get('journal') or item.get('source')}｜{item.get('study_type')}")
    lines.extend(["", "中文新闻："])
    for item in cn_items[:3]:
        lines.append(f"- {title(item)}")
    lines.extend(["", "国际新闻："])
    for item in intl_items[:3]:
        lines.append(f"- {title(item)}")
    lines.append("")
    lines.append("查看完整页面：")
    lines.append(dashboard_url or "请查看 GitHub Pages。")
    lines.append("")
    lines.append("提示：每篇摘要已折叠在网页中，可展开查看中文摘要和推文草稿。")
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
                    "header": {"title": {"tag": "plain_text", "content": "Biomed Radar 今日医学科学新闻已更新"}, "template": "turquoise"},
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
