#!/usr/bin/env python3
"""检测泡泡玛特是否发布新公告/财报（HKEX 披露易）。

流程：
  1. 经 prefix.do 动态解析 Pop Mart(09992) 的 stockId（避免硬编码猜错）。
  2. 经 titlesearchservlet.do 拉取近一年公告标题（返回 JSON）。
  3. 与 data/seen_filings.json 比对，发现新标题则打印并以退出码 10 返回，
     供 GitHub Actions 据此开 issue 提醒更新数据。

设计原则：
  - 仅用标准库（urllib/json/re），Actions 无需安装依赖。
  - 网络/接口异常不致命：失败时打印警告、退出码 0，不阻塞工作流。
  - 首次运行（seen 为空）只建立基线，不误报。
  - 解析失败时打印原始响应片段，便于按 CI 日志校准。

用法:
    python3 scripts/check_filings.py            # 检测，发现新公告退出码 10
    python3 scripts/check_filings.py --baseline # 仅建立/刷新基线，不触发提醒
"""
import datetime
import http.cookiejar
import json
import os
import re
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import load, save  # noqa: E402

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
STOCK_CODE = "09992"
FALLBACK_STOCK_ID = None  # 解析失败时的兜底（如已知可填）
NEW_FILING_EXIT_CODE = 10
SEARCH_PAGE = "https://www1.hkexnews.hk/search/titlesearch.xhtml?lang=en"
PREFIX_URL = "https://www1.hkexnews.hk/search/prefix.do?callback=callback&lang=en&type=A&name={code}&market=SEHK"
SEARCH_URL = "https://www1.hkexnews.hk/search/titlesearchservlet.do"

# HKEX 披露易需要先访问搜索页拿到 JSESSIONID cookie，否则接口返回空。
# 用带 cookie 罐的 opener，首次调用前自动“热身”握手。
_OPENER = None


def _get_opener():
    global _OPENER
    if _OPENER is None:
        jar = http.cookiejar.CookieJar()
        op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
        op.addheaders = [
            ("User-Agent", UA),
            ("Accept", "application/json, text/javascript, text/plain, */*"),
            ("Accept-Language", "en-US,en;q=0.9,zh-CN;q=0.8"),
            ("Referer", SEARCH_PAGE),
            ("X-Requested-With", "XMLHttpRequest"),
        ]
        try:  # 热身：访问搜索页以获取会话 cookie
            op.open(SEARCH_PAGE, timeout=30).read()
        except Exception as e:
            print(f"::warning:: HKEX 会话热身失败（继续尝试）：{e}")
        _OPENER = op
    return _OPENER


def _get(url, timeout=30):
    return _get_opener().open(url, timeout=timeout).read().decode("utf-8", "ignore")


def resolve_stock_id():
    # prefix.do 用 JSONP 回调包裹，带上 callback 参数更稳；正则提取 stockId。
    url = PREFIX_URL.format(code=STOCK_CODE)
    try:
        raw = _get(url)
    except Exception as e:
        print(f"::warning:: stockId 解析请求失败：{e}")
        return FALLBACK_STOCK_ID
    m = re.search(r'"stockId"\s*:\s*"?(\d+)"?', raw)
    if m:
        return m.group(1)
    print(f"::warning:: 未能从 prefix.do 解析 stockId（len={len(raw)}），片段：{raw[:300]!r}")
    return FALLBACK_STOCK_ID


def _find_news_list(obj):
    """在任意 JSON 结构中找到“公告记录列表”（list[dict]）。"""
    if isinstance(obj, list) and obj and isinstance(obj[0], dict):
        return obj
    if isinstance(obj, dict):
        for v in obj.values():
            found = _find_news_list(v)
            if found:
                return found
    return None


def _extract_title_date(d):
    title = date = None
    for k, v in d.items():
        ku = k.upper()
        if title is None and ("TITLE" in ku or ku == "T" or "NEWS_TITLE" in ku):
            title = str(v).strip()
        if date is None and ("DATE" in ku or "TIME" in ku):
            date = str(v).strip()
    return title, date


def fetch_titles(stock_id):
    today = datetime.date.today()
    frm = (today - datetime.timedelta(days=400)).strftime("%Y%m%d")
    to = today.strftime("%Y%m%d")
    params = {
        "sortDir": "0", "sortByOptions": "DateTime", "category": "0",
        "market": "SEHK", "stockId": str(stock_id), "documentType": "-1",
        "fromDate": frm, "toDate": to, "title": "", "searchType": "0",
        "t1code": "-2", "t2Gcode": "-2", "t2code": "-2",
        "rowRange": "100", "lang": "en",
    }
    url = SEARCH_URL + "?" + urllib.parse.urlencode(params)
    try:
        raw = _get(url)
    except Exception as e:
        print(f"::warning:: 公告接口抓取失败（不阻塞）：{e}")
        return None
    # 响应可能是 {"result": "<json-string>"} 或直接 JSON
    try:
        outer = json.loads(raw)
    except json.JSONDecodeError:
        print(f"::warning:: 公告接口返回非 JSON，原始片段：{raw[:300]}")
        return None
    if isinstance(outer, dict) and isinstance(outer.get("result"), str):
        try:
            outer = json.loads(outer["result"])
        except json.JSONDecodeError:
            pass
    items = _find_news_list(outer)
    if not items:
        print(f"::warning:: 未在响应中找到公告列表，结构片段：{json.dumps(outer, ensure_ascii=False)[:300]}")
        return None
    titles = []
    for d in items:
        title, date = _extract_title_date(d)
        if title:
            titles.append((date or "", title))
    return titles


def main():
    baseline_only = "--baseline" in sys.argv
    state = load("seen_filings.json")
    seen = set(state.get("seen", []))
    state["last_checked"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    stock_id = resolve_stock_id()
    if not stock_id:
        print("::warning:: 无可用 stockId，跳过本次检测。")
        save("seen_filings.json", state)
        return 0
    print(f"Pop Mart stockId = {stock_id}")

    titles = fetch_titles(stock_id)
    if titles is None:
        save("seen_filings.json", state)
        return 0

    fetched = [t for _, t in titles]
    print(f"拉取到 {len(fetched)} 条公告标题。")
    new = [t for t in fetched if t not in seen]

    if not seen or baseline_only:
        state["seen"] = sorted(set(fetched) | seen)
        save("seen_filings.json", state)
        print(f"已建立/刷新公告基线，共 {len(state['seen'])} 条。")
        return 0

    state["seen"] = sorted(set(fetched) | seen)
    save("seen_filings.json", state)

    if new:
        print(f"检测到 {len(new)} 条新公告：")
        for t in new:
            print(f"  - {t}")
        gh_out = os.environ.get("GITHUB_OUTPUT")
        if gh_out:
            with open(gh_out, "a", encoding="utf-8") as f:
                f.write("new_filing=true\n")
                f.write("new_titles=" + " / ".join(new[:5]) + "\n")
        return NEW_FILING_EXIT_CODE

    print("无新公告。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
