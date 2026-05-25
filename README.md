# 全医学顶刊与 RCT 研究雷达

面向医学科研、医学新闻、医院公众号和 CGTN 医疗科技选题的全医学/生物医药顶刊正刊与权威 RCT 研究雷达。

本项目每天自动检索 PubMed、顶刊 RSS、bioRxiv、medRxiv 和 arXiv，重点筛选 NEJM、Lancet、JAMA、BMJ、Nature Medicine、Science Translational Medicine、Nature、Science、Cell 及 Lancet/JAMA/Nature/Cell 系列期刊中的 original article、randomized controlled trial、phase 2/3 trial、guideline 和重磅转化医学研究。

本项目不自动发布公众号，只生成可人工审核的医学推文/新闻稿草稿。

## 输出文件

- `data/latest.json`
- `output/briefing.md`
- `output/briefing.txt`
- `output/newsletter.md`
- `index.html`

## 本地运行

```bash
cd ~/AIProjects/biomed-top-journal-radar
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python preview_local.py
python run_daily.py --no-push --no-email
```

## 本地检查

```bash
bash scripts/check_v1.sh
```

成功时会显示：

```text
V1 local check passed
```

## 微信/飞书提醒测试

当前主推送方式叫“微信提醒”，实际优先使用飞书群机器人作为提醒入口。

```bash
export FEISHU_WEBHOOK_URL='你的飞书机器人 webhook'
bash scripts/test_push.sh
```

也预留：

- `WECHAT_WEBHOOK_URL`
- `WECOM_WEBHOOK_URL`

如果 webhook 缺失，流程不会失败，只会提示跳过推送。

## 邮件备份测试

邮件仅作为备份。Gmail 必须使用 App Password，不要使用普通登录密码。

```bash
export SMTP_USER='your@gmail.com'
export SMTP_APP_PASSWORD='Gmail 应用专用密码'
export EMAIL_TO='lipengtao12@gmail.com'
bash scripts/test_email.sh
```

## GitHub Actions

workflow：`.github/workflows/daily-biomed-radar.yml`

- 手动触发：Actions -> Biomed Top Journal Radar -> Run workflow
- 定时触发：每天 UTC 23:40，即北京时间 07:40
- 运行后会更新并提交 `data/latest.json`、`output/briefing.md`、`output/briefing.txt`、`output/newsletter.md`、`index.html`

## GitHub Secrets

建议配置：

- `FEISHU_WEBHOOK_URL`
- `WECOM_WEBHOOK_URL` 可选
- `WECHAT_WEBHOOK_URL` 可选
- `PUBLIC_DASHBOARD_URL`
- `OPENAI_API_KEY` 可选
- `OPENAI_MODEL` 可选，默认 `gpt-4.1-mini`
- `EMAIL_ENABLED` 可选
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_APP_PASSWORD`
- `EMAIL_TO`
- `EMAIL_FROM`

## GitHub Pages

`index.html` 位于仓库根目录。设置路径：

GitHub 仓库 -> Settings -> Pages -> Deploy from a branch -> `main` -> `/root`

预期地址：

https://LPT111.github.io/biomed-top-journal-radar/
