#!/usr/bin/env python3
"""抓取泡泡玛特 (9992.HK) 及对标公司的实时行情快照，写入 data/quote_snapshot.json。

数据源（按优先级，均无需鉴权）：
  1. Yahoo v8 chart 接口  /v8/finance/chart/{sym}  —— 只需浏览器 UA，无需 crumb
  2. Stooq CSV 兜底       https://stooq.com/q/l/?s={sym}&f=...&e=csv

泡泡玛特实时市值 = 股价 × shares_outstanding（取自 peers.json）。
网络/接口异常不致命：失败则保留上次快照并打印警告。仅用标准库。

用法: python3 scripts/fetch_quote.py
"""
import csv
import datetime
import io
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import DATA_DIR, load  # noqa: E402

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

# Yahoo 符号 -> (中文名, Stooq 符号)
TICKERS = {
    "9992.HK": ("泡泡玛特 Pop Mart", "9992.hk"),
    "MAT": ("美泰 Mattel", "mat.us"),
    "HAS": ("孩之宝 Hasbro", "has.us"),
    "8136.T": ("三丽鸥 Sanrio", "8136.jp"),
    "7832.T": ("万代南梦宫 Bandai Namco", "7832.jp"),
    "9896.HK": ("名创优品 MINISO", "9896.hk"),
}


def _get(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "ignore")


def from_yahoo_v8(sym):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=5d"
    data = json.loads(_get(url))
    res = (data.get("chart", {}).get("result") or [None])[0]
    if not res:
        return None
    meta = res.get("meta", {})
    price = meta.get("regularMarketPrice")
    prev = meta.get("chartPreviousClose") or meta.get("previousClose")
    if price is None:
        return None
    change_pct = ((price - prev) / prev) if prev else None
    return {
        "price": price,
        "currency": meta.get("currency"),
        "change_pct": change_pct,
        "source": "yahoo_v8",
    }


def from_stooq(stooq_sym):
    url = f"https://stooq.com/q/l/?s={stooq_sym}&f=sd2t2ohlcvn&h&e=csv"
    text = _get(url)
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows:
        return None
    r = rows[0]
    close = r.get("Close")
    if not close or close in ("N/D", ""):
        return None
    try:
        price = float(close)
    except ValueError:
        return None
    op = r.get("Open")
    change_pct = None
    try:
        if op and op not in ("N/D", ""):
            o = float(op)
            change_pct = (price - o) / o if o else None
    except ValueError:
        pass
    return {"price": price, "currency": None, "change_pct": change_pct, "source": "stooq"}


def fetch_one(sym, stooq_sym):
    # 多源容错：Yahoo 在 CI 的共享 IP 常被限流(429)，Stooq 兜底。
    # 仅当所有源都失败才告警，避免日志噪音。
    errors = []
    for fn, arg in ((from_yahoo_v8, sym), (from_stooq, stooq_sym)):
        try:
            r = fn(arg)
            if r:
                return r
        except Exception as e:
            errors.append(f"{fn.__name__}: {e}")
    print(f"::warning:: {sym} 所有数据源失败：{'; '.join(errors)}")
    return None


def main():
    peers = load("peers.json")
    anchor = peers.get("anchor", {})
    shares = anchor.get("shares_outstanding")
    hkd_usd = anchor.get("hkd_to_usd", 0.128)

    quotes = {}
    for sym, (name, stooq_sym) in TICKERS.items():
        r = fetch_one(sym, stooq_sym)
        if not r:
            print(f"::warning:: {sym} 全部数据源失败，跳过")
            continue
        r["name"] = name
        if sym == "9992.HK" and shares and r.get("price"):
            cur = (r.get("currency") or "HKD").upper()
            usd_price = r["price"] * (hkd_usd if cur == "HKD" else 1)
            r["market_cap_usd_b"] = round(usd_price * shares / 1e9, 1)
        quotes[sym] = r

    path = os.path.join(DATA_DIR, "quote_snapshot.json")
    if not quotes:
        print("::warning:: 行情全部失败，保留上次快照（若有）。")
        return 0

    snapshot = {
        "as_of": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "quotes": quotes,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    print(f"已更新行情快照: {path}")
    for sym, r in quotes.items():
        mc = r.get("market_cap_usd_b")
        mc_s = f"  市值~{mc}B(US$)" if mc else ""
        cp = r.get("change_pct")
        cp_s = f"{cp * 100:+.2f}%" if cp is not None else "—"
        print(f"  {sym:8s} {r['name']:20s} {r['price']} {r.get('currency') or ''}  {cp_s}  [{r['source']}]{mc_s}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
