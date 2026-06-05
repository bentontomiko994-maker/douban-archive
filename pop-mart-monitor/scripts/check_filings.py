#!/usr/bin/env python3
"""检测泡泡玛特是否发布新公告/财报。

策略：抓取 HKEX 披露易上市公司公告标题（公开接口），与 data/seen_filings.json
中已记录的标题比对。发现新标题则打印并以退出码 10 返回，供 GitHub Actions
据此开 issue 提醒人工/Claude 更新数据。

设计原则：
- 仅用标准库（urllib），Actions 无需安装依赖。
- 网络异常不致命：失败时打印警告、退出码 0，不阻塞工作流。
- 首次运行（seen 为空）只建立基线，不误报。

用法:
    python3 scripts/check_filings.py            # 检测，发现新公告退出码 10
    python3 scripts/check_filings.py --baseline # 仅建立/刷新基线，不触发提醒
"""
import datetime
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import load, save  # noqa: E402

# 泡泡玛特 HKEX 股票代码 09992。披露易标题搜索接口（返回 JSON）。
HKEX_STOCK_ID = "53815"  # Pop Mart 在披露易的内部 stockId
HKEX_API = (
    "https://www1.hkexnews.hk/hkexnews/api/internalnews.do"
    "?lang=zh&category=0&market=SEHK&stockId={sid}"
    "&documentType=&fromDate=&toDate=&title="
).format(sid=HKEX_STOCK_ID)

NEW_FILING_EXIT_CODE = 10


def fetch_titles():
    """返回 [(date, title)]；失败返回 None。"""
    req = urllib.request.Request(HKEX_API, headers={"User-Agent": "Mozilla/5.0 pop-mart-monitor"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", "ignore")
    except Exception as e:  # 网络/接口异常 -> 不致命
        print(f"::warning:: 公告接口抓取失败（不阻塞）: {e}")
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print("::warning:: 公告接口返回非 JSON（接口可能变更），跳过本次检测")
        return None
    out = []
    for item in data.get("newsInfoList", []) or []:
        title = (item.get("newsTitle") or "").strip()
        date = (item.get("newsTime") or "").strip()
        if title:
            out.append((date, title))
    return out


def main():
    baseline_only = "--baseline" in sys.argv
    state = load("seen_filings.json")
    seen = set(state.get("seen", []))

    titles = fetch_titles()
    state["last_checked"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    if titles is None:
        save("seen_filings.json", state)
        return 0

    fetched = [t for _, t in titles]
    new = [t for t in fetched if t not in seen]

    # 首次建立基线，或显式 --baseline：吸收全部，不报新
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
        # 供 Actions 读取的输出
        gh_out = os.environ.get("GITHUB_OUTPUT")
        if gh_out:
            with open(gh_out, "a", encoding="utf-8") as f:
                f.write("new_filing=true\n")
                joined = " / ".join(new[:5])
                f.write(f"new_titles={joined}\n")
        return NEW_FILING_EXIT_CODE

    print("无新公告。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
