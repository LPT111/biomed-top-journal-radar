from __future__ import annotations

import json
import os
from typing import Any

import requests


def _fallback(item: dict[str, Any]) -> dict[str, Any]:
    title = item.get("title", "Untitled")
    journal = item.get("journal", "")
    study_type = item.get("study_type", "研究")
    topic_cn = item.get("topic_cn", "综合医学")
    abstract = item.get("abstract", "")
    is_cn = item.get("source_region") == "cn" or item.get("source_language") == "zh"
    short_abs = abstract[:520] + ("..." if len(abstract) > 520 else "")
    translated_title = title if is_cn else f"{topic_cn}研究：{title}"
    brief = f"{journal or item.get('source','来源')} 发布的{topic_cn}相关{study_type}，值得关注其研究设计、核心发现和转化边界。"
    summary = (
        f"这条内容聚焦{topic_cn}。来源为{journal or item.get('source','相关来源')}，类型初步识别为{study_type}。"
        f"摘要信息显示：{short_abs or '当前未抓取到完整摘要，需要打开原文核对研究设计、样本量、主要终点和结论。'}"
        " 该摘要由规则模板生成，适合快速浏览，不替代人工阅读全文。"
    )
    what_they_did = f"围绕{topic_cn}方向开展研究或报道，具体研究对象、干预/暴露因素和主要终点需以原文为准。"
    key_finding = "自动摘要暂不能可靠提取定量结果；建议优先核对主要终点、效应量、安全性和统计学显著性。"
    relevance = "可作为医学科研选题、医院公众号选题或 CGTN 医疗科技报道的候选素材。"
    limitations = "当前为自动抓取与规则总结，未替代人工阅读全文；疗效、样本量、统计学结果、利益冲突和适用人群需进一步核验。"
    quality = "source_chinese" if is_cn else "rule_based"
    draft = (
        f"【医学科学新闻】{translated_title}\n\n"
        f"一、为什么重要\n{brief}\n\n"
        f"二、研究怎么做\n{what_they_did}\n\n"
        f"三、主要发现\n{key_finding}\n\n"
        f"四、对临床/科研的意义\n{relevance}\n\n"
        f"五、需要谨慎解读的地方\n{limitations}\n\n"
        f"六、小满点评\n先把它放进候选池，重点看是否改变诊疗路径、提出新机制或提供可转化技术线索。\n\n"
        f"七、参考信息\n{journal}｜{item.get('published','')}｜{item.get('url','')}"
    )
    return {
        "translated_title_cn": translated_title,
        "translated_summary_cn": summary,
        "chinese_brief_cn": brief[:90],
        "why_it_matters_cn": brief,
        "what_they_did_cn": what_they_did,
        "key_finding_cn": key_finding,
        "caution_cn": limitations,
        "editor_note_cn": "自动生成，适合选题初筛；正式发布前需人工核对。",
        "summary_quality": quality,
        "tweet_title_cn": translated_title,
        "one_sentence_value_cn": brief,
        "ai_summary_cn": summary,
        "clinical_relevance_cn": relevance,
        "limitations_cn": limitations,
        "wechat_draft_cn": draft,
    }


def _openai_summary(item: dict[str, Any]) -> dict[str, Any] | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    prompt = {
        "title": item.get("title", ""),
        "journal": item.get("journal", ""),
        "published": item.get("published", ""),
        "study_type": item.get("study_type", ""),
        "topic_cn": item.get("topic_cn", ""),
        "abstract": item.get("abstract", "")[:3000],
        "source_region": item.get("source_region", ""),
    }
    system = "你是严谨的医学科研编辑。请用简体中文、克制准确地总结医学顶刊/RCT研究，不夸大疗效。输出严格 JSON。"
    user = (
        "请根据以下文献信息生成 JSON，字段为 translated_title_cn, translated_summary_cn, chinese_brief_cn, "
        "why_it_matters_cn, what_they_did_cn, key_finding_cn, caution_cn, editor_note_cn, "
        "tweet_title_cn, one_sentence_value_cn, ai_summary_cn, clinical_relevance_cn, limitations_cn, wechat_draft_cn。"
        "要求：简体中文；translated_summary_cn 200-350字；chinese_brief_cn 50-80字；不夸大结论。"
        "wechat_draft_cn 按“为什么重要/研究怎么做/主要发现/意义/谨慎解读/小满点评/参考信息”组织。\n"
        f"{json.dumps(prompt, ensure_ascii=False)}"
    )
    try:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
            },
            timeout=45,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        data = json.loads(content)
        if all(k in data for k in ["translated_title_cn", "translated_summary_cn", "chinese_brief_cn", "wechat_draft_cn"]):
            data["summary_quality"] = "llm_translated"
            return data
    except Exception:
        return None
    return None


def summarize_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for item in items:
        summary = _openai_summary(item) or _fallback(item)
        merged = dict(item)
        merged.update(summary)
        merged.setdefault("translated_title_cn", merged.get("tweet_title_cn") or merged.get("title", ""))
        merged.setdefault("translated_summary_cn", merged.get("ai_summary_cn", ""))
        merged.setdefault("chinese_brief_cn", merged.get("one_sentence_value_cn", "")[:90])
        merged.setdefault("why_it_matters_cn", merged.get("one_sentence_value_cn", ""))
        merged.setdefault("what_they_did_cn", "请打开原文核对研究设计。")
        merged.setdefault("key_finding_cn", "请打开原文核对主要发现。")
        merged.setdefault("caution_cn", merged.get("limitations_cn", "需人工核验。"))
        merged.setdefault("editor_note_cn", "自动生成，需人工核验。")
        merged.setdefault("summary_quality", "rule_based")
        out.append(merged)
    return out
