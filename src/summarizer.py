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
    short_abs = abstract[:360] + ("..." if len(abstract) > 360 else "")
    one_sentence = f"这是一项发表于 {journal or '相关期刊'} 的{study_type}，主题聚焦{topic_cn}，适合用于判断该领域最新证据变化。"
    summary = f"论文围绕“{title}”展开。基于题名、期刊和摘要信息，研究可能涉及{topic_cn}方向的重要临床或转化问题。摘要要点：{short_abs or '暂无摘要，需打开原文核对研究设计和结论。'}"
    relevance = "可作为医学科研选题、医院公众号选题或 CGTN 医疗科技报道的候选素材；正式解读前建议核对全文、研究对象、主要终点和安全性数据。"
    limitations = "当前为自动抓取与规则总结，未替代人工阅读全文；疗效、样本量、统计学结果和利益冲突需进一步核验。"
    draft = (
        f"【医学顶刊速递】{title}\n\n"
        f"一、为什么重要\n{one_sentence}\n\n"
        f"二、研究怎么做\n请基于全文进一步核对研究设计、纳入人群、干预/暴露因素和主要终点。\n\n"
        f"三、主要发现\n{short_abs or '摘要暂缺，建议打开原文补充。'}\n\n"
        f"四、对临床/科研的意义\n{relevance}\n\n"
        f"五、需要谨慎解读的地方\n{limitations}\n\n"
        f"六、小满点评\n先把它放进候选池，重点看是否改变诊疗路径、提出新机制或提供可转化技术线索。\n\n"
        f"七、参考信息\n{journal}｜{item.get('published','')}｜{item.get('url','')}"
    )
    return {
        "tweet_title_cn": f"论文标题：{title}",
        "one_sentence_value_cn": one_sentence,
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
    }
    system = "你是严谨的医学科研编辑。请用简体中文、克制准确地总结医学顶刊/RCT研究，不夸大疗效。输出严格 JSON。"
    user = (
        "请根据以下文献信息生成 JSON，字段为 tweet_title_cn, one_sentence_value_cn, "
        "ai_summary_cn, clinical_relevance_cn, limitations_cn, wechat_draft_cn。"
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
        if all(k in data for k in ["tweet_title_cn", "one_sentence_value_cn", "ai_summary_cn", "clinical_relevance_cn", "limitations_cn", "wechat_draft_cn"]):
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
        out.append(merged)
    return out
