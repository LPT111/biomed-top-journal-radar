from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"


def _esc(value: Any) -> str:
    return html.escape(str(value or ""))


def _stats(items: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "total": len(items),
        "cn": sum(1 for x in items if x.get("source_region") == "cn"),
        "intl": sum(1 for x in items if x.get("source_region") == "intl"),
        "tier_a": sum(1 for x in items if x.get("journal_tier") == "tier_a"),
        "rct_or_trial": sum(1 for x in items if "trial" in x.get("study_type", "").lower() or x.get("study_type") == "RCT"),
        "translational": sum(1 for x in items if "translational" in x.get("study_type", "").lower() or "mechanism" in x.get("news_angle", "").lower()),
    }


def render_outputs(items: list[dict[str, Any]], errors: list[str] | None = None, generated_at: str | None = None) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    errors = errors or []
    generated_at = generated_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    stats = _stats(items)
    payload = {"generated_at": generated_at, "stats": stats, "items": items, "notes": errors}
    (DATA_DIR / "latest.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "briefing.md").write_text(_briefing_md(items, generated_at, stats, errors), encoding="utf-8")
    (OUTPUT_DIR / "briefing.txt").write_text(_briefing_txt(items, generated_at, stats, errors), encoding="utf-8")
    (OUTPUT_DIR / "newsletter.md").write_text(_newsletter_md(items, generated_at), encoding="utf-8")
    cn_items = [x for x in items if x.get("content_bucket") == "cn_news"][:5]
    intl_items = [x for x in items if x.get("content_bucket") == "intl_news"][:15]
    (OUTPUT_DIR / "cn_news.md").write_text(_section_md("中文医学科学新闻", cn_items), encoding="utf-8")
    (OUTPUT_DIR / "intl_news.md").write_text(_section_md("国际顶刊与医学科学新闻", intl_items), encoding="utf-8")
    (BASE_DIR / "index.html").write_text(_html(items, generated_at, stats, errors), encoding="utf-8")
    if errors:
        (OUTPUT_DIR / "error_report.txt").write_text("\n".join(errors), encoding="utf-8")


def _display_title(item: dict[str, Any]) -> str:
    return item.get("translated_title_cn") or item.get("tweet_title_cn") or item.get("title", "")


def _briefing_md(items: list[dict[str, Any]], generated_at: str, stats: dict[str, Any], notes: list[str]) -> str:
    lines = [
        f"# 全医学科学新闻雷达｜{generated_at}",
        "",
        f"- 今日新闻：{stats['total']} 条",
        f"- 中文来源：{stats['cn']} 条",
        f"- 国际来源：{stats['intl']} 条",
        f"- 顶刊论文：{stats['tier_a']} 条",
        f"- RCT/临床试验：{stats['rct_or_trial']} 条",
        "",
    ]
    for note in notes:
        lines.append(f"> {note}")
    lines.append("## 今日 20 条")
    for i, item in enumerate(items, 1):
        lines.extend([
            f"{i}. {_display_title(item)}",
            f"   - 来源：{item.get('journal') or item.get('source')}｜类型：{item.get('study_type','')}｜分数：{item.get('score','')}",
            f"   - 链接：{item.get('url','')}",
            f"   - 简述：{item.get('chinese_brief_cn','')}",
        ])
    return "\n".join(lines) + "\n"


def _briefing_txt(items: list[dict[str, Any]], generated_at: str, stats: dict[str, Any], notes: list[str]) -> str:
    lines = [
        f"【Biomed Radar】今日医学科学新闻已更新｜{generated_at}",
        f"今日 {stats['total']} 条：中文来源 {stats['cn']} 条｜国际来源 {stats['intl']} 条",
        "",
    ]
    lines.extend(notes)
    for i, item in enumerate(items, 1):
        lines.extend([
            f"{i}. {_display_title(item)}",
            f"{item.get('journal') or item.get('source')}｜{item.get('study_type','')}｜Score {item.get('score','')}",
            f"{item.get('chinese_brief_cn','')}",
            f"{item.get('url','')}",
            "",
        ])
    return "\n".join(lines)


def _newsletter_md(items: list[dict[str, Any]], generated_at: str) -> str:
    lines = [f"# 医学科学新闻推文候选草稿｜{generated_at}", ""]
    for i, item in enumerate(items, 1):
        lines.extend([
            f"## {i}. {_display_title(item)}",
            "",
            item.get("wechat_draft_cn", ""),
            "",
            "---",
            "",
        ])
    return "\n".join(lines)


def _section_md(title: str, items: list[dict[str, Any]]) -> str:
    lines = [f"# {title}", ""]
    for i, item in enumerate(items, 1):
        lines.extend([
            f"{i}. {_display_title(item)}",
            f"   - 来源：{item.get('journal') or item.get('source')}",
            f"   - 时间：{item.get('published','')}",
            f"   - 摘要：{item.get('translated_summary_cn','')}",
            f"   - 链接：{item.get('url','')}",
        ])
    return "\n".join(lines) + "\n"


def _html(items: list[dict[str, Any]], generated_at: str, stats: dict[str, Any], notes: list[str]) -> str:
    headlines = sorted(items, key=lambda x: x.get("score", 0), reverse=True)[:3]
    cn_items = [x for x in items if x.get("content_bucket") == "cn_news"][:5]
    intl_items = [x for x in items if x.get("content_bucket") == "intl_news"][:15]
    note_html = "".join(f"<div class='notice'>{_esc(note)}</div>" for note in notes if "不足" in note)
    headline_html = "".join(_headline(item, i) for i, item in enumerate(headlines, 1))
    cn_html = "".join(_card(item, i, "cn") for i, item in enumerate(cn_items, 1))
    intl_html = "".join(_card(item, i, "intl") for i, item in enumerate(intl_items, 1))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>全医学科学新闻雷达</title>
  <style>
    :root {{ --ink:#10201f; --muted:#667574; --green:#0b5a50; --teal:#0f766e; --blue:#0b4f6c; --line:#dfe8e6; --soft:#f4faf8; --paper:#fff; --amber:#9a6b14; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif; color:var(--ink); background:linear-gradient(180deg,#fff 0%,#f5fbfa 100%); }}
    a {{ color:var(--teal); text-decoration:none; }} a:hover {{ text-decoration:underline; }}
    .wrap {{ width:min(1220px, calc(100% - 32px)); margin:0 auto; padding:28px 0 58px; }}
    .hero {{ border:1px solid var(--line); border-radius:26px; padding:30px; background:#fff; box-shadow:0 18px 48px rgba(16,32,31,.08); }}
    .kicker {{ color:var(--teal); font-weight:900; letter-spacing:.14em; text-transform:uppercase; font-size:12px; }}
    h1 {{ margin:8px 0 6px; color:var(--green); font-size:clamp(34px,5vw,58px); letter-spacing:-.055em; line-height:1.02; }}
    .cn-title {{ color:#1f3431; font-size:22px; font-weight:900; margin-bottom:8px; }}
    .subtitle {{ color:var(--muted); line-height:1.7; margin:0; }}
    .stats {{ display:grid; grid-template-columns:repeat(6,minmax(0,1fr)); gap:10px; margin-top:18px; }}
    .stat {{ border:1px solid var(--line); background:var(--soft); border-radius:16px; padding:12px; }}
    .stat small {{ display:block; color:var(--muted); font-size:12px; margin-bottom:5px; }}
    .stat strong {{ font-size:22px; color:var(--green); }}
    .notice {{ margin-top:12px; border:1px solid #f1d48a; background:#fff8e6; color:#7a5410; border-radius:14px; padding:10px 12px; font-size:13px; font-weight:800; }}
    .section {{ margin-top:22px; }}
    .section-head {{ display:flex; justify-content:space-between; align-items:end; gap:14px; margin-bottom:12px; }}
    .section-head h2 {{ margin:0; color:var(--green); font-size:24px; letter-spacing:-.035em; }}
    .section-head span {{ color:var(--muted); font-size:13px; }}
    .headline-grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; }}
    .headline, .card {{ background:#fff; border:1px solid var(--line); border-radius:18px; padding:16px; box-shadow:0 12px 34px rgba(16,32,31,.055); }}
    .headline h3, .card h3 {{ margin:8px 0 7px; font-size:18px; line-height:1.42; letter-spacing:-.02em; }}
    .meta {{ color:var(--muted); font-size:12px; line-height:1.55; }}
    .brief {{ color:#304845; line-height:1.68; font-size:14px; margin:10px 0; }}
    .tag-row {{ display:flex; flex-wrap:wrap; gap:7px; align-items:center; }}
    .rank {{ background:var(--green); color:#fff; border-radius:999px; padding:5px 9px; font-size:12px; font-weight:900; }}
    .tag {{ border:1px solid var(--line); background:#f8fbfa; border-radius:999px; padding:5px 8px; font-size:12px; color:#31514d; font-weight:800; }}
    .link {{ display:inline-flex; align-items:center; justify-content:center; border-radius:999px; background:var(--green); color:#fff; padding:8px 11px; font-weight:900; font-size:13px; margin-top:4px; }}
    .link:hover {{ background:#083f38; text-decoration:none; }}
    .news-list {{ display:grid; gap:12px; }}
    .english-title {{ color:var(--muted); font-size:13px; line-height:1.5; margin-top:-2px; }}
    details {{ margin-top:10px; border-top:1px solid var(--line); padding-top:10px; }}
    summary {{ cursor:pointer; color:var(--blue); font-weight:900; font-size:13px; }}
    .detail-body {{ margin-top:10px; background:#f8fbfa; border:1px solid var(--line); border-radius:14px; padding:13px; }}
    .detail-body h4 {{ margin:12px 0 5px; color:var(--green); font-size:14px; }}
    .detail-body h4:first-child {{ margin-top:0; }}
    .detail-body p, .detail-body pre {{ margin:0; color:#344947; line-height:1.75; font-size:14px; white-space:pre-wrap; font-family:inherit; }}
    footer {{ text-align:center; color:var(--muted); font-size:12px; margin-top:24px; }}
    @media (max-width:980px) {{ .stats {{ grid-template-columns:repeat(3,1fr); }} .headline-grid {{ grid-template-columns:1fr; }} }}
    @media (max-width:640px) {{ .wrap {{ width:min(100% - 22px,1220px); }} .hero {{ padding:22px; }} .stats {{ grid-template-columns:repeat(2,1fr); }} }}
  </style>
</head>
<body>
  <main class="wrap">
    <header class="hero">
      <div class="kicker">Biomed Top Journal Radar</div>
      <h1>Biomed Top Journal Radar</h1>
      <div class="cn-title">全医学科学新闻雷达</div>
      <p class="subtitle">每日 20 条医学科学新闻｜中文 5 条 · 国际 15 条｜顶刊论文 · RCT · 转化医学 · 生物医药</p>
      <div class="stats">
        <div class="stat"><small>今日新闻</small><strong>{stats['total']}</strong></div>
        <div class="stat"><small>中文来源</small><strong>{stats['cn']}</strong></div>
        <div class="stat"><small>国际来源</small><strong>{stats['intl']}</strong></div>
        <div class="stat"><small>顶刊论文</small><strong>{stats['tier_a']}</strong></div>
        <div class="stat"><small>RCT/临床试验</small><strong>{stats['rct_or_trial']}</strong></div>
        <div class="stat"><small>转化/机制</small><strong>{stats['translational']}</strong></div>
      </div>
      <p class="meta">生成时间：{_esc(generated_at)}</p>
      {note_html}
    </header>
    <section class="section" id="headlines">
      <div class="section-head"><h2>今日头条</h2><span>按分数全局排序 Top 3</span></div>
      <div class="headline-grid">{headline_html}</div>
    </section>
    <section class="section" id="cn-news">
      <div class="section-head"><h2>中文医学科学新闻</h2><span>5 条</span></div>
      <div class="news-list">{cn_html}</div>
    </section>
    <section class="section" id="intl-news">
      <div class="section-head"><h2>国际顶刊与医学科学新闻</h2><span>15 条</span></div>
      <div class="news-list">{intl_html}</div>
    </section>
    <footer>本页面仅供医学科研和医学新闻选题初筛；每篇摘要默认折叠，正式发布前请核对原文。</footer>
  </main>
</body>
</html>"""


def _headline(item: dict[str, Any], rank: int) -> str:
    return f"""
<article class="headline">
  <div class="tag-row"><span class="rank">Top {rank}</span><span class="tag">{_esc(item.get('study_type'))}</span><span class="tag">{_esc(item.get('topic_cn'))}</span><span class="tag">Score {_esc(item.get('score'))}</span></div>
  <h3>{_esc(_display_title(item))}</h3>
  <div class="meta">{_esc(item.get('journal') or item.get('source'))}｜{_esc(item.get('published'))}</div>
  <p class="brief">{_esc(item.get('chinese_brief_cn'))}</p>
  <a class="link" href="{_esc(item.get('url'))}" target="_blank" rel="noopener">打开原文</a>
</article>"""


def _card(item: dict[str, Any], rank: int, region: str) -> str:
    pmid = f"PMID：{_esc(item.get('pmid'))}" if item.get("pmid") else ""
    doi = f"DOI：{_esc(item.get('doi'))}" if item.get("doi") else ""
    english = "" if region == "cn" else f"<div class='english-title'>{_esc(item.get('title'))}</div>"
    return f"""
<article class="card">
  <div class="tag-row">
    <span class="rank">{rank}</span>
    <span class="tag">{_esc(item.get('news_origin'))}</span>
    <span class="tag">{_esc(item.get('study_type'))}</span>
    <span class="tag">{_esc(item.get('topic_cn'))}</span>
    <span class="tag">Score {_esc(item.get('score'))}</span>
  </div>
  <h3>{_esc(_display_title(item))}</h3>
  {english}
  <div class="meta">{_esc(item.get('journal') or item.get('source'))}｜{_esc(item.get('published'))}｜{pmid} {doi}</div>
  <p class="brief">{_esc(item.get('chinese_brief_cn'))}</p>
  <a class="link" href="{_esc(item.get('url'))}" target="_blank" rel="noopener">原文链接</a>
  <details>
    <summary>查看中文摘要与推文草稿</summary>
    <div class="detail-body">
      <h4>中文摘要</h4>
      <p>{_esc(item.get('translated_summary_cn'))}</p>
      <h4>为什么重要</h4>
      <p>{_esc(item.get('why_it_matters_cn'))}</p>
      <h4>研究怎么做</h4>
      <p>{_esc(item.get('what_they_did_cn'))}</p>
      <h4>主要发现</h4>
      <p>{_esc(item.get('key_finding_cn'))}</p>
      <h4>需要谨慎解读</h4>
      <p>{_esc(item.get('caution_cn'))}</p>
      <h4>人工审核前推文草稿</h4>
      <pre>{_esc(item.get('wechat_draft_cn'))}</pre>
    </div>
  </details>
</article>"""
