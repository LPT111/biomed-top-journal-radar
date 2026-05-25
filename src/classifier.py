from __future__ import annotations

from typing import Any


STUDY_RULES = [
    ("randomized_controlled_trial", "RCT", ["randomized controlled trial", "randomised controlled trial", "randomized", "double-blind", "placebo-controlled"]),
    ("phase_3_trial", "Phase 3 trial", ["phase 3", "phase iii"]),
    ("phase_2_trial", "Phase 2 trial", ["phase 2", "phase ii"]),
    ("clinical_trial", "Clinical trial", ["clinical trial", "trial"]),
    ("guideline", "Guideline", ["guideline", "recommendation", "consensus"]),
    ("meta_analysis", "Meta-analysis", ["meta-analysis", "systematic review"]),
    ("review", "Review", ["review"]),
    ("editorial", "Editorial/comment", ["editorial", "comment", "perspective", "correspondence", "department of error", "correction", "erratum", "news"]),
    ("preprint", "Preprint", ["preprint", "biorxiv", "medrxiv", "arxiv"]),
]


ANGLE_RULES = [
    ("改变临床实践", ["practice changing", "overall survival", "primary endpoint", "superior", "noninferiority"]),
    ("权威 RCT", ["randomized", "double-blind", "placebo-controlled"]),
    ("新药临床试验", ["phase 3", "phase iii", "phase 2", "drug", "therapy"]),
    ("诊疗指南更新", ["guideline", "recommendation", "consensus"]),
    ("重大机制突破", ["mechanism", "pathway", "single-cell", "spatial", "omics"]),
    ("医疗 AI", ["artificial intelligence", "machine learning", "large language model", "diagnostic algorithm"]),
    ("细胞/基因治疗", ["gene therapy", "cell therapy", "crispr", "car-t", "rna therapy"]),
    ("公共卫生", ["public health", "population", "screening", "prevention"]),
    ("安全性警示", ["adverse event", "safety", "risk", "toxicity"]),
    ("阴性但重要研究", ["did not improve", "no significant", "negative", "failed to meet"]),
]


def classify_item(item: dict[str, Any], topics: dict[str, Any]) -> dict[str, Any]:
    text = " ".join([
        item.get("title", ""),
        item.get("abstract", ""),
        item.get("journal", ""),
        " ".join(item.get("publication_types", []) or []),
        item.get("source", ""),
    ]).lower()

    study_key, study_label = "original_research", "Original research"
    for key, label, needles in STUDY_RULES:
        if any(needle in text for needle in needles):
            study_key, study_label = key, label
            break
    if study_key == "original_research" and any(word in text for word in ["mechanism", "translational", "animal model", "cell"]):
        study_key, study_label = "translational_research", "Translational research"

    best_topic = "other"
    best_label = "综合医学"
    best_hits = 0
    for topic_key, topic in topics.items():
        hits = sum(1 for kw in topic.get("keywords", []) if kw.lower() in text)
        if hits > best_hits:
            best_topic = topic_key
            best_label = topic.get("label_cn", topic_key)
            best_hits = hits

    angle = "顶刊正刊"
    for label, needles in ANGLE_RULES:
        if any(needle in text for needle in needles):
            angle = label
            break

    item["study_type_key"] = study_key
    item["study_type"] = study_label
    item["topic"] = best_topic
    item["topic_cn"] = best_label
    item["disease_area"] = best_topic
    item["news_angle"] = angle
    return item
