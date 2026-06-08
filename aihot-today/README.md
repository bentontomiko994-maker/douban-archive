# AI 今日热榜 (aihot-today)

每日自动抓取全球 AI 热点资讯，生成结构化汇总报告。
灵感来源：[aihot.today](https://aihot.today/)

最新报告见 **[`reports/aihot-today-report.md`](reports/aihot-today-report.md)**。

## 数据来源

| 来源 | 内容 | 接口 |
| --- | --- | --- |
| **Hacker News** | AI/ML 热门讨论帖（按热度排序） | Algolia Search API（公开） |
| **HuggingFace Daily Papers** | 每日精选 AI 论文 | `huggingface.co/api/daily_papers`（公开） |
| **arXiv** | cs.AI / cs.LG / cs.CL 最新预印本 | RSS 订阅（公开） |

三个来源均无需鉴权，仅用 Python 标准库。

## 目录结构

```
aihot-today/
├── data/
│   ├── daily_snapshot.json   # 最新抓取快照（fetch_news.py 生成）
│   └── sources.json          # 数据来源登记
├── scripts/
│   ├── lib.py                # 共享工具（加载/保存）
│   ├── fetch_news.py         # 抓取三路数据 → daily_snapshot.json
│   └── generate_report.py   # 快照 → reports/aihot-today-report.md
└── reports/
    └── aihot-today-report.md # 自动生成的汇总报告
```

## 本地使用

```bash
# 抓取今日数据（需外网）
python3 aihot-today/scripts/fetch_news.py

# 生成报告（无需外网，使用现有快照）
python3 aihot-today/scripts/generate_report.py
```

## 自动化 (GitHub Actions)

工作流定义见 [`.github/workflows/aihot-today.yml`](../.github/workflows/aihot-today.yml)：

- **定时**：每日 08:00 UTC（北京时间 16:00）自动抓取并刷新报告
- **触发即跑**：`aihot-today/**` 有改动时自动重算
- **自动回写**：刷新后的快照与报告自动提交回仓库

> 注意：GitHub 的 `schedule` 定时器**只在默认分支生效**。本工作流合并到 `main`
> 后定时任务才会真正启动；在功能分支上可用「Actions → Run workflow」手动触发。
