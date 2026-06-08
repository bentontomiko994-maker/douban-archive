#!/usr/bin/env python3
"""抓取今日 AI 热点资讯，写入 data/daily_snapshot.json。

数据源（均为公开接口，无需鉴权）：
  1. Hacker News Algolia Search API  — AI/ML 热门帖子（按热度排序）
  2. HuggingFace Daily Papers API   — 每日精选 AI 论文
  3. arXiv cs.AI + cs.LG RSS        — 最新 AI/ML 预印本

设计原则：
  - 仅用标准库（urllib/json/xml.etree），无需 pip install。
  - 网络/接口异常不致命：失败则打印警告、跳过该源，不阻塞工作流。
  - 每次运行全量覆盖快照，保留 as_of 时间戳。

用法：
    python3 aihot-today/scripts/fetch_news.py
"""
import datetime
import json
import os
import sys
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import save_snapshot  # noqa: E402

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def _get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "ignore")


def fetch_hn(n=20):
    """Hacker News Algolia：过去 24h 内 AI/ML 相关热门故事。"""
    cutoff = int((datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=36)).timestamp())
    keywords = "artificial intelligence OR LLM OR GPT OR Claude OR machine learning OR deep learning OR neural network OR AI"
    params = urllib.parse.urlencode({
        "query": keywords,
        "tags": "story",
        "numericFilters": f"created_at_i>{cutoff}",
        "hitsPerPage": n,
        "attributesToRetrieve": "objectID,title,url,points,num_comments,created_at",
    })
    url = f"https://hn.algolia.com/api/v1/search?{params}"
    try:
        data = json.loads(_get(url))
        items = []
        for h in data.get("hits", []):
            items.append({
                "title": h.get("title", ""),
                "url": h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
                "points": h.get("points", 0),
                "comments": h.get("num_comments", 0),
                "hn_url": f"https://news.ycombinator.com/item?id={h.get('objectID')}",
                "created_at": h.get("created_at", ""),
            })
        items.sort(key=lambda x: (x["points"] or 0) + (x["comments"] or 0) * 2, reverse=True)
        print(f"HN: 获取到 {len(items)} 条")
        return items
    except Exception as e:
        print(f"::warning:: HN 抓取失败：{e}")
        return []


def fetch_hf_papers(n=10):
    """HuggingFace Daily Papers API：今日精选论文。"""
    url = "https://huggingface.co/api/daily_papers"
    try:
        data = json.loads(_get(url))
        items = []
        for p in data[:n]:
            paper = p.get("paper", {})
            items.append({
                "title": paper.get("title", ""),
                "authors": [a.get("name", "") for a in paper.get("authors", [])[:4]],
                "abstract": paper.get("summary", "")[:300].replace("\n", " ") + ("…" if len(paper.get("summary", "")) > 300 else ""),
                "url": f"https://huggingface.co/papers/{paper.get('id', '')}",
                "arxiv_url": f"https://arxiv.org/abs/{paper.get('id', '')}",
                "upvotes": p.get("numComments", 0),
                "published": paper.get("publishedAt", ""),
            })
        print(f"HuggingFace Papers: 获取到 {len(items)} 篇")
        return items
    except Exception as e:
        print(f"::warning:: HuggingFace Papers 抓取失败：{e}")
        return []


def fetch_arxiv(n=10):
    """arXiv cs.AI + cs.LG：最新预印本 RSS。"""
    results = []
    for cat in ("cs.AI", "cs.LG", "cs.CL"):
        url = f"http://export.arxiv.org/rss/{cat}"
        try:
            raw = _get(url)
            root = ET.fromstring(raw)
            ns = {"": "http://purl.org/rss/1.0/", "dc": "http://purl.org/dc/elements/1.1/"}
            items_xml = root.findall(".//item", ns) or root.findall(".//item")
            for item in items_xml[:n]:
                title_el = item.find("title") or item.find("{http://purl.org/rss/1.0/}title")
                link_el = item.find("link") or item.find("{http://purl.org/rss/1.0/}link")
                desc_el = item.find("description") or item.find("{http://purl.org/rss/1.0/}description")
                title = (title_el.text or "").strip()
                link = (link_el.text or "").strip()
                abstract = ""
                if desc_el is not None and desc_el.text:
                    abstract = desc_el.text.strip()[:280].replace("\n", " ") + "…"
                if title:
                    results.append({
                        "title": title,
                        "url": link,
                        "abstract": abstract,
                        "category": cat,
                    })
        except Exception as e:
            print(f"::warning:: arXiv {cat} RSS 抓取失败：{e}")
        if len(results) >= n:
            break
    seen_titles = set()
    deduped = []
    for r in results:
        t = r["title"][:80]
        if t not in seen_titles:
            seen_titles.add(t)
            deduped.append(r)
    print(f"arXiv: 获取到 {len(deduped)} 篇（去重后）")
    return deduped[:n]


def main():
    print(f"开始抓取 AI 今日热点 ({datetime.date.today()})…")
    hn = fetch_hn(20)
    papers = fetch_hf_papers(10)
    arxiv = fetch_arxiv(10)

    snapshot = {
        "as_of": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "date": datetime.date.today().isoformat(),
        "hn_stories": hn,
        "hf_papers": papers,
        "arxiv_papers": arxiv,
    }
    save_snapshot(snapshot)
    print(f"快照已写入 data/daily_snapshot.json")
    print(f"  HN 故事: {len(hn)}  |  HF 论文: {len(papers)}  |  arXiv: {len(arxiv)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
