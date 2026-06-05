#!/usr/bin/env python3
"""判断今天是否处于泡泡玛特业绩披露窗口期（确定性触发，不依赖任何抓取）。

泡泡玛特业绩披露时间高度规律（年报约 3 月下旬、中报约 8 月下旬）。
本脚本读取 data/earnings_calendar.json，若今天落在某个预计披露日的
[日期-before, 日期+after] 窗口内，则向 GITHUB_OUTPUT 写出 in_window=true，
供工作流开提醒 issue。纯日期逻辑，可本地测试。

用法:
    python3 scripts/earnings_window.py
    python3 scripts/earnings_window.py --today=2026-08-20   # 测试指定日期
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import load  # noqa: E402


def main():
    cal = load("earnings_calendar.json")
    today = datetime.date.today()
    for arg in sys.argv[1:]:
        if arg.startswith("--today="):
            today = datetime.date.fromisoformat(arg.split("=", 1)[1])

    before = datetime.timedelta(days=cal.get("window_days_before", 3))
    after = datetime.timedelta(days=cal.get("window_days_after", 7))
    labels = cal.get("labels", {})

    hits = []
    for d in cal.get("expected_results", []):
        try:
            ed = datetime.date.fromisoformat(d)
        except ValueError:
            continue
        if ed - before <= today <= ed + after:
            hits.append(f"{d}（{labels.get(d, '业绩')}）")

    if hits:
        msg = "; ".join(hits)
        print(f"✅ 处于业绩披露窗口期：{msg}")
        gh_out = os.environ.get("GITHUB_OUTPUT")
        if gh_out:
            with open(gh_out, "a", encoding="utf-8") as f:
                f.write("in_window=true\n")
                f.write(f"window_msg={msg}\n")
    else:
        print(f"当前（{today}）不在业绩披露窗口期。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
