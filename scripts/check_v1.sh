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
test -s data/latest.json

python run_daily.py --no-push --no-email

test -s index.html
test -s output/briefing.md
test -s output/briefing.txt
test -s output/newsletter.md
test -s data/latest.json
python -m json.tool data/latest.json >/dev/null

echo "V1 local check passed"
