#!/usr/bin/env python3
"""读取 data/ 下的结构化数据，自动生成泡泡玛特监控汇总报告到 reports/。

每次财报发布后：更新 data/*.json -> 运行本脚本 -> 报告自动刷新。
用法:
    python3 scripts/generate_report.py
仅依赖标准库，无需 pip install。
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import REPORTS_DIR, load, latest_annual, num, pct, prev_annual  # noqa: E402


def section_summary(fin, ov):
    cur = latest_annual(fin)
    prev = prev_annual(fin)
    lines = ["## 一、执行摘要（最新财报）", ""]
    lines.append(f"**最新财报口径：{cur['period']}**（发布于 {cur.get('release_date', '—')}）")
    lines.append("")
    lines.append("| 指标 | 数值 | 同比 |")
    lines.append("| --- | --- | --- |")
    lines.append(f"| 营业收入 | {num(cur['revenue'], ' 亿元')} | {pct(cur['revenue_yoy'])} |")
    lines.append(f"| 净利润 | {num(cur['net_profit'], ' 亿元')} | {pct(cur['net_profit_yoy'])} |")
    lines.append(f"| 毛利率 | {pct(cur['gross_margin'], signed=False)} | — |")
    lines.append(f"| 海外收入 | {num(cur['overseas_revenue'], ' 亿元')} | — |")
    lines.append(f"| 海外占比 | {pct(cur['overseas_share'], signed=False)} | — |")
    lines.append(f"| 门店总数 | {num(cur['stores_total'], ' 家')} | 海外 {num(cur['stores_overseas'])} 家 |")
    lines.append(f"| 覆盖国家/地区 | {num(cur['countries'])} | — |")
    lines.append("")
    if cur.get("note"):
        lines.append(f"> {cur['note']}")
        lines.append("")
    if prev:
        rev_mult = cur["revenue"] / prev["revenue"] if prev["revenue"] else None
        if rev_mult:
            lines.append(
                f"对比上一年度 {prev['period']}（营收 {num(prev['revenue'], ' 亿元')}），"
                f"营收增至 **{rev_mult:.2f}x**；海外占比由 {pct(prev['overseas_share'], signed=False)} "
                f"升至 {pct(cur['overseas_share'], signed=False)}。"
            )
            lines.append("")
    return lines


def section_same_store(fin):
    lines = ["## 二、同店 / 线下销售", ""]
    lines.append(
        "> 说明：泡泡玛特未持续披露标准化的“同店销售额(SSS)”单一指标，"
        "市场通常以**线下零售店渠道收入增速**作为同店有机增长的代理指标"
        "（门店数小幅增加而渠道收入大幅增长，即体现强同店增长）。"
    )
    lines.append("")
    lines.append("| 期次 | 线下零售收入 | 同比 | 门店总数 | 中国门店 |")
    lines.append("| --- | --- | --- | --- | --- |")
    for p in fin["periods"]:
        if p.get("offline_retail_revenue") is not None or p["type"] == "annual":
            lines.append(
                f"| {p['period']} | {num(p.get('offline_retail_revenue'), ' 亿元')} | "
                f"{pct(p.get('offline_retail_yoy'))} | {num(p.get('stores_total'), ' 家')} | "
                f"{num(p.get('stores_china'), ' 家')} |"
            )
    lines.append("")
    return lines


def section_overseas(ov):
    g = ov["global_summary"]
    lines = ["## 三、海外扩张：开店数量、国家与区域营收", ""]
    lines.append(
        f"截至 **{ov['as_of']}**，全球门店 **{num(g['stores_total'])} 家**"
        f"（中国 {num(g['stores_china'])} 家 / 海外 {num(g['stores_overseas'])} 家，海外当期净增 {num(g.get('overseas_net_add'))} 家），"
        f"覆盖 **{num(g['countries_and_regions'])} 个国家与地区**，机器人商店 {num(g.get('vending_machines'))} 台。"
    )
    lines.append("")
    lines.append("### 分区域营收、增速与门店")
    lines.append("")
    lines.append("| 区域 | 营收(亿元) | 同比 | 门店数 | 当期净增 | 核心市场 |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for r in ov["by_region_fy2025"]:
        lines.append(
            f"| {r['region']} | {num(r['revenue'])} | {pct(r['revenue_yoy'])} | "
            f"{num(r['stores'])} | {num(r['net_add'])} | {r['core_markets']} |"
        )
    lines.append("")
    prof = ov.get("overseas_profitability", {})
    if prof:
        lines.append(
            f"**海外盈利能力（{prof.get('as_of')} 口径）**：毛利率 {pct(prof.get('gross_margin'), signed=False)}，"
            f"净利率 {pct(prof.get('net_margin'), signed=False)}。{prof.get('note', '')}"
        )
        lines.append("")
    lines.append(f"**覆盖国家示例**：{'、'.join(ov.get('country_footprint_examples', []))}。")
    lines.append("")
    return lines


def section_peers(peers):
    a = peers["anchor"]
    lines = ["## 四、同业对比", ""]
    lines.append(f"对标基准（估值数据 as of {peers.get('valuation_as_of')}）：")
    lines.append("")

    def row(c):
        return (
            f"| {c['name']} | {c.get('ticker', '—')} | "
            f"{num(c.get('revenue'))} {c.get('revenue_unit', '')} | "
            f"{num(c.get('market_cap_usd_b'), ' B')} | {num(c.get('pe'))} |"
        )

    lines.append("### 4.1 全球玩具/IP 巨头（估值锚）")
    lines.append("")
    lines.append("| 公司 | 代码 | 营收 | 市值(US$B) | PE(TTM) |")
    lines.append("| --- | --- | --- | --- | --- |")
    lines.append(
        f"| **{a['name']}** | {a['ticker']} | {a['revenue']} {a['revenue_unit']} · "
        f"{a['revenue_local']} | {num(a.get('market_cap_usd_b'), ' B')} | {num(a.get('pe'))} |"
    )
    for c in peers["peers"]["global_toy_ip_giants"]:
        lines.append(row(c))
    lines.append("")
    lines.append(f"> 泡泡玛特估值说明：{a.get('note', '')}")
    lines.append("")

    lines.append("### 4.2 中国潮玩 / IP 同行")
    lines.append("")
    lines.append("| 公司 | 代码 | 营收 | 全球门店 | 备注 |")
    lines.append("| --- | --- | --- | --- | --- |")
    for c in peers["peers"]["china_trendy_toys"]:
        lines.append(
            f"| {c['name']} | {c.get('ticker', '—')} | {num(c.get('revenue'))} {c.get('revenue_unit', '')} | "
            f"{num(c.get('global_stores'))} | {c.get('note', '')} |"
        )
    lines.append("")

    lines.append("### 4.3 出海 / 零售可比")
    lines.append("")
    for c in peers["peers"]["going_global_retail_comps"]:
        lines.append(f"- **{c['name']}**（{c.get('ticker', '—')}）：海外营收 {c.get('overseas_revenue', '—')}，"
                     f"全球门店 {num(c.get('global_stores'))}。{c.get('note', '')}")
    lines.append("")
    lines.append(
        "**横向解读**：泡泡玛特 FY2025 营收（~US$5.1B）已接近美泰、超过孩之宝，"
        "但增速（+184.7%）与海外占比（43.8%）远高于传统巨头；其 IP 变现 + 高毛利模式"
        "更接近三丽鸥的轻资产授权逻辑，但自营零售与出海速度更激进。"
    )
    lines.append("")
    return lines


def load_quote_snapshot():
    """行情快照可选；不存在或损坏则返回 None。"""
    path = os.path.join(os.path.dirname(REPORTS_DIR), "data", "quote_snapshot.json")
    try:
        with open(path, encoding="utf-8") as f:
            import json
            return json.load(f)
    except (FileNotFoundError, ValueError):
        return None


def section_quote(snap):
    q = snap.get("quotes", {})
    if not q:
        return []
    lines = ["## 五、实时行情快照", ""]
    lines.append(f"_行情更新于 {snap.get('as_of', '—')}_")
    lines.append("")
    lines.append("| 代码 | 公司 | 现价 | 涨跌 | 实时市值(US$B) |")
    lines.append("| --- | --- | --- | --- | --- |")
    for sym, r in q.items():
        cp = r.get("change_pct")
        cp_s = f"{cp * 100:+.2f}%" if cp is not None else "—"
        price = f"{r.get('price')} {r.get('currency') or ''}".strip()
        mc = r.get("market_cap_usd_b")
        lines.append(f"| {sym} | {r.get('name', '')} | {price} | {cp_s} | {num(mc)} |")
    lines.append("")
    return lines


def main():
    fin = load("financials.json")
    ov = load("overseas_stores.json")
    peers = load("peers.json")
    sources = load("sources.json")
    snap = load_quote_snapshot()

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    out = []
    out.append("# 泡泡玛特 (Pop Mart, 9992.HK) 监控汇总报告")
    out.append("")
    out.append(f"_自动生成于 {now} · 由 `scripts/generate_report.py` 基于 `data/` 渲染 · 非投资建议_")
    out.append("")
    out += section_summary(fin, ov)
    out += section_same_store(fin)
    out += section_overseas(ov)
    out += section_peers(peers)
    if snap:
        out += section_quote(snap)

    out.append("## 六、数据来源")
    out.append("")
    for s in sources.get("primary", []):
        out.append(f"- [一手] [{s['title']}]({s['url']}) — {s.get('publisher', '')}")
    for s in sources.get("media", [])[:6]:
        out.append(f"- [媒体] [{s['title']}]({s['url']}) — {s.get('publisher', '')}")
    out.append("")
    out.append(f"> {sources.get('disclaimer', '')}")
    out.append("")

    os.makedirs(REPORTS_DIR, exist_ok=True)
    path = os.path.join(REPORTS_DIR, "pop-mart-report.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"已生成报告: {path} ({len(out)} 行)")


if __name__ == "__main__":
    main()
