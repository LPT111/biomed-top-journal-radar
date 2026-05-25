# Biomed Top Journal Radar V1

## V1 功能

- 检索 PubMed、顶刊 RSS、bioRxiv、medRxiv、arXiv。
- 聚焦全医学顶刊、RCT、Phase 2/3 trial、guideline、重大转化医学研究。
- 自动分类疾病领域、研究类型、新闻角度。
- 自动评分并去重，输出 Top 10。
- 生成 `data/latest.json`、`output/briefing.md`、`output/briefing.txt`、`output/newsletter.md`、`index.html`。
- 支持飞书群机器人作为“微信提醒”入口，预留企业微信/微信 webhook。
- 支持可选邮件备份。
- 支持 GitHub Actions 每天北京时间 07:40 自动运行和手动触发。
- 不自动发布公众号，仅生成可人工审核草稿。

## 本地运行

```bash
cd ~/AIProjects/biomed-top-journal-radar
python preview_local.py
python run_daily.py --no-push --no-email
```

## 本地检查

```bash
bash scripts/check_v1.sh
```

## 微信/飞书提醒测试

```bash
export FEISHU_WEBHOOK_URL='你的 webhook'
bash scripts/test_push.sh
```

## 邮件测试

```bash
export SMTP_USER='your@gmail.com'
export SMTP_APP_PASSWORD='Gmail 应用专用密码'
export EMAIL_TO='lipengtao12@gmail.com'
bash scripts/test_email.sh
```

## GitHub Secrets

- `FEISHU_WEBHOOK_URL`
- `WECOM_WEBHOOK_URL` 可选
- `WECHAT_WEBHOOK_URL` 可选
- `PUBLIC_DASHBOARD_URL`
- `OPENAI_API_KEY` 可选
- `OPENAI_MODEL`
- `EMAIL_ENABLED`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_APP_PASSWORD`
- `EMAIL_TO`
- `EMAIL_FROM`

## 输出文件

- `data/latest.json`
- `output/briefing.md`
- `output/briefing.txt`
- `output/newsletter.md`
- `index.html`

## 发布记录

- `v1.0.0`：全医学顶刊与 RCT 研究雷达首个公开版本。

## V1.1 计划

1. 每日两更。
2. 多 cron fallback。
3. push-state 去重。
4. RCT 结构化解析。
5. 期刊 IF/JCR/CAS 分区匹配。
6. 按主题订阅。
7. 周报。
