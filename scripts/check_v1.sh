#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

python3 --version
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python -m py_compile run_daily.py preview_local.py src/*.py
python preview_local.py

test -s index.html
test -s output/briefing.md
test -s output/briefing.txt
test -s output/newsletter.md
test -s output/cn_news.md
test -s output/intl_news.md
test -s data/latest.json

python run_daily.py --no-push --no-email

test -s index.html
test -s output/briefing.md
test -s output/briefing.txt
test -s output/newsletter.md
test -s output/cn_news.md
test -s output/intl_news.md
test -s data/latest.json
python -m json.tool data/latest.json >/dev/null

python - <<'PY'
import json
data=json.load(open("data/latest.json"))
items=data["items"]
assert len(items)==20, len(items)
assert sum(1 for x in items if x.get("content_bucket")=="cn_news")==5
assert sum(1 for x in items if x.get("content_bucket")=="intl_news")==15
assert all(x.get("translated_title_cn") for x in items)
assert all(x.get("chinese_brief_cn") for x in items)
assert all(x.get("translated_summary_cn") for x in items)
PY

echo "V1.2 news20 local check passed"
