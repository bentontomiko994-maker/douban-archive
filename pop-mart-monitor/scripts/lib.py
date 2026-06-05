"""共享工具：数据加载与格式化。仅依赖 Python 标准库。"""
import json
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")


def load(name):
    """加载 data/ 下的 JSON 文件。"""
    with open(os.path.join(DATA_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def save(name, obj):
    with open(os.path.join(DATA_DIR, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def pct(x, signed=True):
    """小数 -> 百分比字符串。0.18 -> '+18.0%'。None -> '—'。"""
    if x is None:
        return "—"
    s = f"{x * 100:.1f}%"
    if signed and x >= 0:
        s = "+" + s
    return s


def num(x, suffix=""):
    """数值 -> 字符串，None -> '—'。"""
    if x is None:
        return "—"
    if isinstance(x, float) and x.is_integer():
        return f"{int(x)}{suffix}"
    return f"{x}{suffix}"


def find_period(financials, period):
    for p in financials["periods"]:
        if p["period"] == period:
            return p
    return None


def latest_annual(financials):
    annuals = [p for p in financials["periods"] if p["type"] == "annual"]
    return annuals[-1] if annuals else None


def prev_annual(financials):
    annuals = [p for p in financials["periods"] if p["type"] == "annual"]
    return annuals[-2] if len(annuals) >= 2 else None
