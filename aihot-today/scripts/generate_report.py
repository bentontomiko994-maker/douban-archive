#!/usr/bin/env python3
"""读取 data/daily_snapshot.json，自动生成 AI 今日热榜报告到 reports/。

用法：
    python3 aihot-today/scripts/generate_report.py
仅依赖标准库，无需 pip install。
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import REPORTS_DIR, load, load_snapshot  # noqa: E402


def section_hn(stories):
    lines = ["## 一、Hacker News · AI 热门讨论", ""]
    if not stories:
        lines.append("_暂无数据（抓取失败或今日无相关帖子）_")
        lines.append("")
        return lines
    lines.append("| # | 标题 | 热度 | 评论 |")
    lines.append("| --- | --- | --- | --- |")
    for i, s in enumerate(stories[:15], 1):
        title = s.get("title", "—")[:80]
        url = s.get("url", "")
        hn_url = s.get("hn_url", url)
        points = s.get("points") or 0
        comments = s.get("comments") or 0
        title_md = f"[{title}]({url})" if url else title
        lines.append(f"| {i} | {title_md} （[HN]({hn_url})）| {points} pts | {comments} |")
    lines.append("")
    return lines


def section_hf_papers(papers):
    lines = ["## 二、HuggingFace · 今日精选论文", ""]
    if not papers:
        lines.append("_暂无数据（抓取失败或今日无推荐论文）_")
        lines.append("")
        return lines
    for i, p in enumerate(papers[:10], 1):
        title = p.get("title", "—")
        url = p.get("url", "")
        authors = ", ".join(p.get("authors", []))
        abstract = p.get("abstract", "")
        upvotes = p.get("upvotes") or 0
        lines.append(f"### {i}. [{title}]({url})")
        if authors:
            lines.append(f"_作者：{authors}_")
        if abstract:
            lines.append(f"> {abstract}")
        if upvotes:
            lines.append(f"👍 {upvotes} upvotes")
        lines.append("")
    return lines


def section_arxiv(papers):
    lines = ["## 三、arXiv · 最新预印本 (cs.AI / cs.LG / cs.CL)", ""]
    if not papers:
        lines.append("_暂无数据（抓取失败）_")
        lines.append("")
        return lines
    for i, p in enumerate(papers[:10], 1):
        title = p.get("title", "—")[:100]
        url = p.get("url", "")
        cat = p.get("category", "")
        abstract = p.get("abstract", "")
        lines.append(f"**{i}.** [{title}]({url})" + (f"  `[{cat}]`" if cat else ""))
        if abstract:
            lines.append(f"> {abstract}")
        lines.append("")
    return lines


def main():
    snap = load_snapshot()
    sources = load("sources.json")

    as_of = snap.get("as_of", "—")
    date = snap.get("date", datetime.date.today().isoformat())
    now_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    hn = snap.get("hn_stories", [])
    hf = snap.get("hf_papers", [])
    arxiv = snap.get("arxiv_papers", [])

    out = []
    out.append("# AI 今日热榜 (aihot.today) 每日汇总报告")
    out.append("")
    out.append(f"_生成于 {now_utc} · 数据快照时间 {as_of[:16]} UTC · 每日自动更新_")
    out.append("")
    out.append(f"**📅 日期：{date}**  |  "
               f"HN 故事 {len(hn)} 条  |  HF 论文 {len(hf)} 篇  |  arXiv {len(arxiv)} 篇")
    out.append("")

    out += section_hn(hn)
    out += section_hf_papers(hf)
    out += section_arxiv(arxiv)

    out.append("## 四、数据来源")
    out.append("")
    for s in sources.get("sources", []):
        out.append(f"- [{s['name']}]({s['url']}) — {s.get('desc', '')}")
    out.append("")
    out.append(f"> {sources.get('disclaimer', '')}")
    out.append("")

    os.makedirs(REPORTS_DIR, exist_ok=True)
    path = os.path.join(REPORTS_DIR, "aihot-today-report.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"已生成报告: {path} ({len(out)} 行)")


if __name__ == "__main__":
    main()
