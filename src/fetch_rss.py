from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import feedparser
import requests


TIMEOUT = 25


def _contains_topic(text: str, topics: dict[str, Any]) -> bool:
    low = text.lower()
    for topic in topics.values():
        for keyword in topic.get("keywords", []):
            if keyword.lower() in low:
                return True
    trial_terms = ["randomized", "phase 3", "phase iii", "clinical trial", "guideline", "translational"]
    return any(term in low for term in trial_terms)


def fetch_top_journal_rss(journals: dict[str, Any], topics: dict[str, Any], errors: list[str] | None = None) -> list[dict[str, Any]]:
    errors = errors if errors is not None else []
    items: list[dict[str, Any]] = []
    for source in journals.get("rss", []):
        try:
            feed = feedparser.parse(source["url"])
            if getattr(feed, "bozo", False) and not feed.entries:
                raise RuntimeError(getattr(feed, "bozo_exception", "RSS parse failed"))
            for entry in feed.entries[:25]:
                title = getattr(entry, "title", "").strip()
                summary = getattr(entry, "summary", "").strip()
                url = getattr(entry, "link", "").strip()
                text = f"{title} {summary}"
                if not title or not url or not _contains_topic(text, topics):
                    continue
                items.append({
                    "source": "Top journal RSS",
                    "source_region": "intl",
                    "source_language": "en",
                    "news_origin": "Journal RSS",
                    "content_bucket": "intl_news",
                    "topic": "",
                    "topic_cn": "",
                    "id": url,
                    "pmid": "",
                    "doi": "",
                    "title": title,
                    "journal": source["name"],
                    "published": getattr(entry, "published", "") or getattr(entry, "updated", ""),
                    "authors": [],
                    "abstract": summary,
                    "url": url,
                    "publication_types": ["RSS"],
                })
        except Exception as exc:
            errors.append(f"RSS {source.get('name', source.get('url'))}: {exc!r}")
    return items


def fetch_preprints(topics: dict[str, Any], errors: list[str] | None = None) -> list[dict[str, Any]]:
    errors = errors if errors is not None else []
    today = date.today()
    start = (today - timedelta(days=7)).isoformat()
    end = today.isoformat()
    items: list[dict[str, Any]] = []
    for server in ("biorxiv", "medrxiv"):
        url = f"https://api.biorxiv.org/details/{server}/{start}/{end}/0"
        try:
            resp = requests.get(url, timeout=TIMEOUT)
            resp.raise_for_status()
            for row in resp.json().get("collection", [])[:120]:
                title = row.get("title", "")
                abstract = row.get("abstract", "")
                if not _contains_topic(f"{title} {abstract}", topics):
                    continue
                doi = row.get("doi", "")
                items.append({
                    "source": server,
                    "source_region": "intl",
                    "source_language": "en",
                    "news_origin": "Preprint",
                    "content_bucket": "intl_news",
                    "topic": "",
                    "topic_cn": "",
                    "id": doi or title,
                    "pmid": "",
                    "doi": doi,
                    "title": title,
                    "journal": server,
                    "published": row.get("date", ""),
                    "authors": [row.get("authors", "")],
                    "abstract": abstract,
                    "url": f"https://doi.org/{doi}" if doi else row.get("url", ""),
                    "publication_types": ["Preprint"],
                })
        except Exception as exc:
            errors.append(f"{server}: {exc!r}")
    return items


def fetch_arxiv(topics: dict[str, Any], errors: list[str] | None = None) -> list[dict[str, Any]]:
    errors = errors if errors is not None else []
    query = " OR ".join([
        "medical AI",
        "clinical trial",
        "biomedicine",
        "drug discovery",
        "large language model medicine",
    ])
    url = "http://export.arxiv.org/api/query"
    try:
        feed = feedparser.parse(f"{url}?search_query=all:{query.replace(' ', '+')}&start=0&max_results=30&sortBy=submittedDate&sortOrder=descending")
        out = []
        for entry in feed.entries:
            title = getattr(entry, "title", "").strip()
            summary = getattr(entry, "summary", "").strip()
            if not _contains_topic(f"{title} {summary}", topics):
                continue
            out.append({
                "source": "arXiv",
                "source_region": "intl",
                "source_language": "en",
                "news_origin": "Preprint",
                "content_bucket": "intl_news",
                "topic": "",
                "topic_cn": "",
                "id": getattr(entry, "id", title),
                "pmid": "",
                "doi": "",
                "title": title,
                "journal": "arXiv",
                "published": getattr(entry, "published", ""),
                "authors": [a.get("name", "") for a in getattr(entry, "authors", [])],
                "abstract": summary,
                "url": getattr(entry, "link", ""),
                "publication_types": ["Preprint"],
            })
        return out
    except Exception as exc:
        errors.append(f"arXiv: {exc!r}")
        return []
