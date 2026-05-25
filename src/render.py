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
        "tier_a": sum(1 for x in items if x.get("journal_tier") == "tier_a"),
        "rct_or_trial": sum(1 for x in items if "trial" in x.get("study_type", "").lower() or x.get("study_type") == "RCT"),
        "preprint": sum(1 for x in items if x.get("source", "").lower() in {"biorxiv", "medrxiv", "arxiv"}),
    }


def render_outputs(items: list[dict[str, Any]], errors: list[str] | None = None, generated_at: str | None = None) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    errors = errors or []
    generated_at = generated_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    stats = _stats(items)
    payload = {"generated_at": generated_at, "stats": stats, "items": items, "errors": errors}
    (DATA_DIR / "latest.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "briefing.md").write_text(_briefing_md(items, generated_at, stats), encoding="utf-8")
    (OUTPUT_DIR / "briefing.txt").write_text(_briefing_txt(items, generated_at, stats), encoding="utf-8")
    (OUTPUT_DIR / "newsletter.md").write_text(_newsletter_md(items, generated_at), encoding="utf-8")
    (BASE_DIR / "index.html").write_text(_html(items, generated_at, stats), encoding="utf-8")
    if errors:
        (OUTPUT_DIR / "error_report.txt").write_text("\n".join(errors), encoding="utf-8")


def _briefing_md(items: list[dict[str, Any]], generated_at: str, stats: dict[str, Any]) -> str:
    lines = [
        f"# 全医学顶刊与 RCT 研究雷达｜{generated_at}",
        "",
        f"- 今日筛选：{stats['total']} 篇",
        f"- 顶刊 A 档：{stats['tier_a']} 篇",
        f"- RCT/临床试验：{stats['rct_or_trial']} 篇",
        "",
        "## 最值得关注",
    ]
    if not items:
        lines.append("本次未抓取到符合条件的文献。")
    for i, item in enumerate(items[:10], 1):
        lines.extend([
            f"{i}. {item.get('title','')}",
            f"   - 期刊：{item.get('journal','')}｜类型：{item.get('study_type','')}｜分数：{item.get('score','')}",
            f"   - 链接：{item.get('url','')}",
            f"   - 价值：{item.get('one_sentence_value_cn','')}",
        ])
    return "\n".join(lines) + "\n"


def _briefing_txt(items: list[dict[str, Any]], generated_at: str, stats: dict[str, Any]) -> str:
    lines = [
        f"【全医学顶刊与 RCT 研究雷达】{generated_at}",
        f"今日筛选：{stats['total']} 篇｜顶刊A档：{stats['tier_a']}｜RCT/临床试验：{stats['rct_or_trial']}",
        "",
    ]
    if not items:
        lines.append("本次未抓取到符合条件的文献。")
    for i, item in enumerate(items[:10], 1):
        lines.extend([
            f"{i}. {item.get('title','')}",
            f"期刊：{item.get('journal','')}｜类型：{item.get('study_type','')}｜分数：{item.get('score','')}",
            f"链接：{item.get('url','')}",
            f"价值：{item.get('one_sentence_value_cn','')}",
            "",
        ])
    return "\n".join(lines)


def _newsletter_md(items: list[dict[str, Any]], generated_at: str) -> str:
    lines = [f"# 医学顶刊推文候选草稿｜{generated_at}", ""]
    if not items:
        lines.append("本次暂无候选推文。")
    for i, item in enumerate(items, 1):
        lines.extend([
            f"## {i}. {item.get('tweet_title_cn','')}",
            "",
            item.get("wechat_draft_cn", ""),
            "",
            "---",
            "",
        ])
    return "\n".join(lines)


def _html(items: list[dict[str, Any]], generated_at: str, stats: dict[str, Any]) -> str:
    cards = "\n".join(_card(item, i) for i, item in enumerate(items, 1)) or "<section class='empty'>本次未抓取到符合条件的文献。</section>"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>全医学顶刊与 RCT 研究雷达</title>
  <style>
    :root {{ --ink:#10201f; --muted:#657172; --green:#0b5a50; --teal:#0f766e; --line:#dfe8e6; --soft:#f4faf8; --blue:#0b4f6c; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif; color:var(--ink); background:linear-gradient(180deg,#ffffff 0%,#f6fbfa 100%); }}
    .wrap {{ width:min(1180px, calc(100% - 32px)); margin:0 auto; padding:28px 0 56px; }}
    header {{ border:1px solid var(--line); border-radius:24px; padding:28px; background:#fff; box-shadow:0 18px 48px rgba(16,32,31,.08); }}
    .kicker {{ color:var(--teal); font-weight:800; letter-spacing:.14em; text-transform:uppercase; font-size:12px; }}
    h1 {{ margin:10px 0 8px; font-size:clamp(32px,5vw,54px); letter-spacing:-.055em; color:var(--green); }}
    .subtitle {{ color:var(--muted); font-size:16px; line-height:1.7; margin:0; }}
    .stats {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin:18px 0 6px; }}
    .stat {{ background:var(--soft); border:1px solid var(--line); border-radius:16px; padding:14px; }}
    .stat small {{ display:block; color:var(--muted); margin-bottom:5px; }}
    .stat strong {{ font-size:24px; color:var(--green); }}
    .grid {{ display:grid; gap:16px; margin-top:18px; }}
    .card {{ background:#fff; border:1px solid var(--line); border-radius:20px; padding:20px; box-shadow:0 14px 36px rgba(16,32,31,.06); }}
    .card-top {{ display:flex; gap:10px; flex-wrap:wrap; align-items:center; margin-bottom:12px; }}
    .rank {{ width:34px; height:34px; border-radius:50%; background:var(--green); color:#fff; display:inline-flex; align-items:center; justify-content:center; font-weight:900; }}
    .tag {{ border:1px solid var(--line); background:#f8fbfa; border-radius:999px; padding:6px 9px; font-size:12px; color:#31514d; font-weight:800; }}
    h2 {{ margin:8px 0 8px; font-size:22px; line-height:1.35; letter-spacing:-.025em; }}
    .meta {{ color:var(--muted); font-size:13px; line-height:1.6; }}
    .link {{ display:inline-flex; margin:12px 0; padding:9px 12px; border-radius:999px; background:var(--green); color:#fff; font-weight:900; text-decoration:none; }}
    .link:hover {{ text-decoration:none; background:#083f38; }}
    .section {{ margin-top:13px; padding-top:13px; border-top:1px solid var(--line); }}
    .section h3 {{ margin:0 0 6px; color:var(--blue); font-size:15px; }}
    .section p, .section pre {{ margin:0; color:#344947; line-height:1.75; font-size:14px; white-space:pre-wrap; font-family:inherit; }}
    .empty {{ padding:34px; text-align:center; color:var(--muted); border:1px dashed var(--line); border-radius:18px; margin-top:20px; background:#fff; }}
    footer {{ color:var(--muted); text-align:center; font-size:12px; margin-top:24px; }}
    @media (max-width:760px) {{ .stats {{ grid-template-columns:1fr 1fr; }} header {{ padding:22px; }} }}
  </style>
</head>
<body>
  <main class="wrap">
    <header>
      <div class="kicker">Biomed Top Journal Radar</div>
      <h1>全医学顶刊与 RCT 研究雷达</h1>
      <p class="subtitle">Top journals · RCTs · translational biomedicine · AI-assisted draft</p>
      <div class="stats">
        <div class="stat"><small>生成时间</small><strong>{_esc(generated_at)}</strong></div>
        <div class="stat"><small>今日筛选</small><strong>{stats['total']}</strong></div>
        <div class="stat"><small>顶刊 A 档</small><strong>{stats['tier_a']}</strong></div>
        <div class="stat"><small>RCT/试验</small><strong>{stats['rct_or_trial']}</strong></div>
      </div>
    </header>
    <section class="grid">{cards}</section>
    <footer>本页面仅生成可人工审核的医学推文/新闻稿草稿，不自动发布公众号；正式引用前请核对原文。</footer>
  </main>
</body>
</html>"""


def _card(item: dict[str, Any], rank: int) -> str:
    pmid = f"PMID：{_esc(item.get('pmid'))}" if item.get("pmid") else ""
    doi = f"DOI：{_esc(item.get('doi'))}" if item.get("doi") else ""
    return f"""
<article class="card">
  <div class="card-top">
    <span class="rank">{rank}</span>
    <span class="tag">{_esc(item.get('journal_tier','unranked'))}</span>
    <span class="tag">{_esc(item.get('study_type','Other'))}</span>
    <span class="tag">{_esc(item.get('topic_cn','综合医学'))}</span>
    <span class="tag">Score {_esc(item.get('score',0))}</span>
  </div>
  <h2>{_esc(item.get('title'))}</h2>
  <div class="meta">{_esc(item.get('journal'))}｜{_esc(item.get('published'))}｜{pmid} {doi}</div>
  <a class="link" href="{_esc(item.get('url'))}" target="_blank" rel="noopener">打开原文</a>
  <div class="section"><h3>一句话价值</h3><p>{_esc(item.get('one_sentence_value_cn'))}</p></div>
  <div class="section"><h3>AI 中文总结</h3><p>{_esc(item.get('ai_summary_cn'))}</p></div>
  <div class="section"><h3>临床/科研意义</h3><p>{_esc(item.get('clinical_relevance_cn'))}</p></div>
  <div class="section"><h3>局限性</h3><p>{_esc(item.get('limitations_cn'))}</p></div>
  <div class="section"><h3>人工审核前推文草稿</h3><pre>{_esc(item.get('wechat_draft_cn'))}</pre></div>
</article>"""
