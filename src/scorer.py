from __future__ import annotations

import re
from typing import Any


def normalize_title(title: str) -> str:
    title = title.lower()
    title = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", title)
    return title


def journal_tier(journal: str, journals: dict[str, Any]) -> str:
    low = (journal or "").lower()
    for tier in ("tier_a", "tier_b", "tier_c"):
        for name in journals.get(tier, []):
            if name.lower() == low or name.lower() in low or low in name.lower():
                return tier
    return "unranked"


def score_item(item: dict[str, Any], journals: dict[str, Any], scoring: dict[str, Any]) -> dict[str, Any]:
    text = f"{item.get('title','')} {item.get('abstract','')}".lower()
    tier = journal_tier(item.get("journal", ""), journals)
    score = scoring.get("journal_tier", {}).get(tier, 0)
    study_key = item.get("study_type_key", "original_research")
    score += scoring.get("study_type", {}).get(study_key, 0)

    if re.search(r"\bn\s*=\s*[\d,]+", text) or re.search(r"\b[\d,]{3,}\s+(patients|participants|adults|children)\b", text):
        score += scoring.get("news_value", {}).get("large_sample", 8)
    if any(term in text for term in ["primary endpoint", "primary end point", "overall survival", "progression-free survival"]):
        score += scoring.get("news_value", {}).get("positive_primary_endpoint", 8)
    if any(term in text for term in ["adverse event", "serious adverse", "safety warning", "toxicity"]):
        score += scoring.get("news_value", {}).get("safety_warning", 8)
    if any(term in text for term in ["china", "chinese", "asia", "multicenter"]):
        score += scoring.get("news_value", {}).get("china_relevance", 6)
    if any(term in text for term in ["glp-1", "car-t", "adc", "crispr", "rna therapy", "large language model", "ai"]):
        score += scoring.get("news_value", {}).get("hot_biotech", 5)
    if item.get("source", "").lower() in {"biorxiv", "medrxiv", "arxiv"}:
        score += scoring.get("study_type", {}).get("preprint", -8)
    if item.get("study_type_key") == "editorial":
        score += scoring.get("study_type", {}).get("editorial", -5) - 35
    if item.get("source") == "Top journal RSS" and not item.get("pmid") and not item.get("doi"):
        score -= 6
    if item.get("abstract"):
        score += 3
    if item.get("doi"):
        score += 2
    if item.get("pmid"):
        score += 2

    item["journal_tier"] = tier
    if item.get("source_region") == "cn":
        score += 18
        item["journal_tier"] = "cn_source"
    item["score"] = int(score)
    return item


def dedupe_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    for item in items:
        key = ""
        if item.get("doi"):
            key = f"doi:{item['doi'].lower()}"
        elif item.get("pmid"):
            key = f"pmid:{item['pmid']}"
        else:
            key = f"title:{normalize_title(item.get('title', ''))}"
        if not key or key == "title:":
            continue
        current = seen.get(key)
        if current is None or item.get("score", 0) > current.get("score", 0):
            seen[key] = item
    return list(seen.values())


def rank_items(items: list[dict[str, Any]], journals: dict[str, Any], scoring: dict[str, Any], limit: int = 10) -> list[dict[str, Any]]:
    scored = [score_item(item, journals, scoring) for item in items]
    deduped = dedupe_items(scored)
    deduped.sort(key=lambda x: (x.get("score", 0), x.get("published", "")), reverse=True)
    return deduped[:limit]
