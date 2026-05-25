from __future__ import annotations

import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]


def send_email(items: list[dict[str, Any]], generated_at: str = "") -> bool:
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_APP_PASSWORD")
    if not user or not password:
        print("Email skipped because SMTP credentials are missing.")
        return False

    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", "587"))
    sender = os.getenv("EMAIL_FROM", user)
    recipient = os.getenv("EMAIL_TO", "lipengtao12@gmail.com")
    dashboard_url = os.getenv("PUBLIC_DASHBOARD_URL", "")

    msg = MIMEMultipart()
    msg["Subject"] = f"【全医学顶刊与 RCT 雷达】{generated_at} 最新结果"
    msg["From"] = sender
    msg["To"] = recipient
    body_lines = [
        f"生成时间：{generated_at}",
        f"筛选文献数量：{len(items)}",
        f"网页链接：{dashboard_url or '见附件 index.html'}",
        "",
    ]
    for i, item in enumerate(items[:10], 1):
        body_lines.extend([
            f"{i}. {item.get('title','')}",
            f"期刊：{item.get('journal','')}｜类型：{item.get('study_type','')}｜分数：{item.get('score','')}",
            f"链接：{item.get('url','')}",
            f"总结：{item.get('one_sentence_value_cn','')}",
            "",
        ])
    msg.attach(MIMEText("\n".join(body_lines), "plain", "utf-8"))

    for rel in ["output/briefing.md", "output/briefing.txt", "output/newsletter.md", "data/latest.json", "index.html"]:
        path = BASE_DIR / rel
        if path.exists():
            part = MIMEApplication(path.read_bytes(), Name=path.name)
            part["Content-Disposition"] = f'attachment; filename="{path.name}"'
            msg.attach(part)

    with smtplib.SMTP(host, port, timeout=30) as smtp:
        smtp.starttls()
        smtp.login(user, password)
        smtp.sendmail(sender, [recipient], msg.as_string())
    print("Email sent.")
    return True
