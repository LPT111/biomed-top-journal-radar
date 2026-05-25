from __future__ import annotations

from typing import Any
from urllib.parse import quote_plus

import feedparser


CN_QUERIES = [
    "医学研究 临床试验 新药",
    "细胞治疗 基因治疗 肿瘤免疫",
    "医疗AI 脑科学 干细胞 外泌体",
    "公共卫生 重大疾病 医学科技",
    "国家卫健委 疾控 医学 科研",
]


def _topic_hint(title: str, summary: str, topics: dict[str, Any]) -> tuple[str, str]:
    text = f"{title} {summary}".lower()
    for key, topic in topics.items():
        for kw in topic.get("keywords", []):
            if kw.lower() in text or kw in title or kw in summary:
                return key, topic.get("label_cn", key)
    cn_rules = [
        ("oncology", "肿瘤/血液肿瘤", ["肿瘤", "癌", "免疫治疗", "car-t", "adc"]),
        ("medical_ai", "医疗AI/数字医学", ["医疗ai", "人工智能", "大模型", "算法"]),
        ("biotech_gene_cell_therapy", "生物医药/细胞与基因治疗", ["细胞治疗", "基因治疗", "干细胞", "外泌体", "新药"]),
        ("infectious_disease", "感染/疫苗", ["感染", "疫苗", "疾控", "传染病"]),
        ("neuroscience", "神经科学/神经疾病", ["脑科学", "神经", "阿尔茨海默", "帕金森"]),
        ("public_health", "公共卫生/流行病学", ["公共卫生", "筛查", "流行病"]),
    ]
    for key, label, needles in cn_rules:
        if any(n in title.lower() or n in summary.lower() for n in needles):
            return key, label
    return "public_health", "公共卫生/流行病学"


def fetch_chinese_news(topics: dict[str, Any], errors: list[str] | None = None) -> list[dict[str, Any]]:
    errors = errors if errors is not None else []
    items: list[dict[str, Any]] = []
    urls = []
    for query in CN_QUERIES:
        q = quote_plus(query)
        urls.append(("Google News CN", f"https://news.google.com/rss/search?q={q}+when:7d&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"))
        urls.append(("Bing News CN", f"https://www.bing.com/news/search?q={q}&format=rss"))

    for source, url in urls:
        try:
            feed = feedparser.parse(url)
            if getattr(feed, "bozo", False) and not feed.entries:
                raise RuntimeError(getattr(feed, "bozo_exception", "RSS parse failed"))
            for entry in feed.entries[:12]:
                title = getattr(entry, "title", "").strip()
                summary = getattr(entry, "summary", "").strip()
                link = getattr(entry, "link", "").strip()
                if not title or not link:
                    continue
                topic, topic_cn = _topic_hint(title, summary, topics)
                items.append({
                    "source": source,
                    "source_region": "cn",
                    "source_language": "zh",
                    "news_origin": "Chinese biomedical news",
                    "content_bucket": "cn_news",
                    "topic": topic,
                    "topic_cn": topic_cn,
                    "id": link,
                    "pmid": "",
                    "doi": "",
                    "title": title,
                    "translated_title_cn": title,
                    "journal": source,
                    "published": getattr(entry, "published", "") or getattr(entry, "updated", ""),
                    "authors": [],
                    "abstract": summary,
                    "url": link,
                    "publication_types": ["News"],
                    "study_type": "Medical news",
                    "study_type_key": "original_research",
                    "summary_quality": "source_chinese",
                })
        except Exception as exc:
            errors.append(f"{source}: {exc!r}")
    return items
