from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path

import yaml

from src.classifier import classify_item
from src.email_sender import send_email
from src.fetch_chinese import fetch_chinese_news
from src.fetch_pubmed import fetch_pubmed
from src.fetch_rss import fetch_arxiv, fetch_preprints, fetch_top_journal_rss
from src.notifier import send_push
from src.render import render_outputs
from src.scorer import rank_items
from src.selector import select_news_20
from src.summarizer import summarize_items


BASE_DIR = Path(__file__).resolve().parent


def load_yaml(path: str):
    return yaml.safe_load((BASE_DIR / path).read_text(encoding="utf-8"))


def load_config():
    return {
        "journals": load_yaml("config/journals.yaml"),
        "topics": load_yaml("config/topics.yaml"),
        "scoring": load_yaml("config/scoring.yaml"),
    }


def preview_items() -> list[dict]:
    from preview_local import sample_items
    return sample_items()


def run_pipeline(use_preview: bool = False) -> tuple[list[dict], list[str], str]:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    config = load_config()
    errors: list[str] = []
    if use_preview:
        raw_items = preview_items()
    else:
        raw_items = []
        raw_items.extend(fetch_chinese_news(config["topics"], errors))
        raw_items.extend(fetch_pubmed(config["journals"], config["topics"], errors))
        raw_items.extend(fetch_top_journal_rss(config["journals"], config["topics"], errors))
        raw_items.extend(fetch_preprints(config["topics"], errors))
        raw_items.extend(fetch_arxiv(config["topics"], errors))
        if len(raw_items) < 20:
            errors.append("Live sources returned fewer than 20 candidates; preview fallback items were used to keep the page complete.")
            raw_items.extend(preview_items())

    classified = [classify_item(item, config["topics"]) for item in raw_items if item.get("title") and item.get("url")]
    ranked = rank_items(classified, config["journals"], config["scoring"], limit=500)
    selected, selection_notes = select_news_20(ranked)
    summarized = summarize_items(selected)
    render_outputs(summarized, errors + selection_notes, generated_at)
    return summarized, errors + selection_notes, generated_at


def email_test() -> int:
    items, _, generated_at = run_pipeline(use_preview=True)
    send_email(items, generated_at)
    return 0


def push_test() -> int:
    items, _, generated_at = run_pipeline(use_preview=True)
    send_push(items, generated_at)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Biomed Top Journal Radar")
    parser.add_argument("--no-push", action="store_true")
    parser.add_argument("--no-email", action="store_true")
    parser.add_argument("--email-test", action="store_true")
    parser.add_argument("--push-test", action="store_true")
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()

    if args.email_test:
        return email_test()
    if args.push_test:
        return push_test()

    items, errors, generated_at = run_pipeline(use_preview=args.preview)
    if not args.no_push:
        send_push(items, generated_at)
    if os.getenv("EMAIL_ENABLED", "false").lower() == "true" and not args.no_email:
        send_email(items, generated_at)

    print(json.dumps({"items": len(items), "errors": len(errors), "generated_at": generated_at}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
