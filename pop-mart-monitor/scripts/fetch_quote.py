#!/usr/bin/env python3
"""抓取泡泡玛特 (9992.HK) 及对标公司的实时行情快照，写入 data/quote_snapshot.json。

数据源：Yahoo Finance 公开行情接口（无需鉴权）。仅用标准库。
网络/接口异常不致命：失败则保留上次快照并打印警告。

用法:
    python3 scripts/fetch_quote.py
"""
import datetime
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import DATA_DIR  # noqa: E402

TICKERS = {
    "9992.HK": "泡泡玛特 Pop Mart",
    "MAT": "美泰 Mattel",
    "HAS": "孩之宝 Hasbro",
    "8136.T": "三丽鸥 Sanrio",
    "7832.T": "万代南梦宫 Bandai Namco",
    "9896.HK": "名创优品 MINISO",
}
YQ = "https://query1.finance.yahoo.com/v7/finance/quote?symbols={syms}"


def fetch():
    url = YQ.format(syms=",".join(TICKERS))
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 pop-mart-monitor"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8", "ignore"))
    except Exception as e:
        print(f"::warning:: 行情抓取失败（不阻塞）: {e}")
        return None
    rows = {}
    for q in data.get("quoteResponse", {}).get("result", []):
        sym = q.get("symbol")
        rows[sym] = {
            "name": TICKERS.get(sym, sym),
            "price": q.get("regularMarketPrice"),
            "currency": q.get("currency"),
            "market_cap": q.get("marketCap"),
            "pe_trailing": q.get("trailingPE"),
            "change_pct": q.get("regularMarketChangePercent"),
        }
    return rows


def main():
    rows = fetch()
    path = os.path.join(DATA_DIR, "quote_snapshot.json")
    if rows is None:
        if os.path.exists(path):
            print("保留上次行情快照。")
        return 0
    snapshot = {
        "as_of": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source": "Yahoo Finance",
        "quotes": rows,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    print(f"已更新行情快照: {path}")
    for sym, r in rows.items():
        mc = r["market_cap"]
        mc_s = f"{mc / 1e9:.1f}B" if mc else "—"
        print(f"  {sym:8s} {r['name']:20s} {r['price']} {r['currency']}  市值~{mc_s}  PE {r.get('pe_trailing')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
