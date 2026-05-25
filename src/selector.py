from __future__ import annotations

from typing import Any


def select_news_20(items: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    notes: list[str] = []
    ordered = sorted(items, key=lambda x: (x.get("score", 0), x.get("published", "")), reverse=True)
    cn_items = [x for x in ordered if x.get("source_region") == "cn"]
    intl_items = [x for x in ordered if x.get("source_region") == "intl"]

    selected_cn = cn_items[:5]
    selected_intl = intl_items[:15]

    if len(selected_cn) < 5:
        need = 5 - len(selected_cn)
        notes.append("中文来源不足，已由国际来源补位。")
        used = {x.get("id") for x in selected_cn + selected_intl}
        fill = [dict(x, replacement_reason="中文来源不足，国际来源补位") for x in intl_items if x.get("id") not in used][:need]
        selected_cn.extend(fill)

    if len(selected_intl) < 15:
        need = 15 - len(selected_intl)
        notes.append("国际来源不足，已由其他来源补位。")
        used = {x.get("id") for x in selected_cn + selected_intl}
        fill = [dict(x, replacement_reason="国际来源不足，其他来源补位") for x in ordered if x.get("id") not in used][:need]
        selected_intl.extend(fill)

    selected = (selected_cn[:5] + selected_intl[:15])[:20]
    if len(selected) < 20 and ordered:
        used = {x.get("id") for x in selected}
        selected.extend([x for x in ordered if x.get("id") not in used][:20 - len(selected)])

    for index, item in enumerate(selected, 1):
        item["rank"] = index
        if index <= 5:
            item["content_bucket"] = "cn_news"
        else:
            item["content_bucket"] = "intl_news"
    return selected[:20], notes
