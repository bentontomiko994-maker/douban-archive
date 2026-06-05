# 泡泡玛特监控系统 (Pop Mart Monitor)

对泡泡玛特（Pop Mart, **9992.HK**）进行**及时追踪 + 自动汇总**的轻量系统。
每次财报发布后，更新数据层即可自动刷新汇总报告，并提供与同业的横向对比。

> ⚠️ 仅用于信息追踪与研究，**不构成任何投资建议**。

## 它能回答的问题

- **同店 / 线下销售变化** — 以线下零售渠道收入增速作为同店有机增长代理指标
- **海外开店数量及国家** — 全球门店、海外门店、覆盖国家、分区域净增
- **海外门店营收 / 利润** — 美洲 / 亚太 / 欧洲分区域营收、增速、海外毛利率与净利率
- **全公司汇总** — 每次财报后自动汇总营收、利润、毛利率、IP 结构、海外占比等
- **同业对比** — 中国潮玩同行、全球玩具/IP 巨头、出海可比、估值/股价四个维度

最新生成的报告见 **[`reports/pop-mart-report.md`](reports/pop-mart-report.md)**。

## 目录结构

```
pop-mart-monitor/
├── data/                     # 结构化数据层（人维护 + 脚本刷新）
│   ├── financials.json       #   各期财务（营收/利润/毛利/海外占比/门店）
│   ├── overseas_stores.json  #   海外分区域营收与门店、国家覆盖、海外盈利能力
│   ├── peers.json            #   对标公司（4 类）数据
│   ├── sources.json          #   数据来源登记（可溯源）
│   ├── seen_filings.json     #   已知公告基线（check_filings 维护）
│   └── quote_snapshot.json   #   行情快照（fetch_quote 生成，自动）
├── scripts/                  # 纯标准库，无需 pip install
│   ├── lib.py                #   加载/格式化工具
│   ├── generate_report.py    #   数据 -> reports/pop-mart-report.md
│   ├── check_filings.py      #   检测 HKEX 新公告，发现则退出码 10
│   └── fetch_quote.py        #   抓取 9992.HK 及同业实时行情
└── reports/
    └── pop-mart-report.md    # 自动生成的汇总报告
```

## 工作流程

```
新财报发布
   │
   ├─(自动) GitHub Actions 定时检测 HKEX 公告 ──发现新公告──► 自动开 issue 提醒
   │
   ├─(人工/Claude) 更新 data/*.json 中的最新数字
   │
   └─► python3 scripts/generate_report.py ──► 刷新 reports/pop-mart-report.md
```

## 本地使用

```bash
# 重新生成汇总报告（任何环境都能跑，无网络依赖）
python3 pop-mart-monitor/scripts/generate_report.py

# 抓取实时行情快照（需要外网）
python3 pop-mart-monitor/scripts/fetch_quote.py

# 检测是否有新公告（需要外网；发现新公告退出码为 10）
python3 pop-mart-monitor/scripts/check_filings.py
```

## 自动化 (GitHub Actions)

工作流定义见 [`.github/workflows/pop-mart-monitor.yml`](../.github/workflows/pop-mart-monitor.yml)：

- **定时**：每周一基线刷新；**3 月 / 8 月**（年报、中报窗口）每日运行
- **触发即跑**：`pop-mart-monitor/**` 有改动时自动重算
- **新财报检测**：检测到 HKEX 新公告自动开 issue 提醒更新数据
- **自动回写**：刷新后的报告/行情快照自动提交回仓库

> 注意：GitHub 的 `schedule` 定时器**只在默认分支生效**。本工作流合并到 `main`
> 后定时任务才会真正启动；在功能分支上可用「Actions → Run workflow」手动触发。

## 每次财报后如何更新（约 2 分钟）

1. 在 `data/financials.json` 的 `periods` 追加一条最新期次（营收、利润、毛利率、海外占比、门店数）。
2. 在 `data/overseas_stores.json` 更新 `as_of` 与 `by_region_*` 分区域营收/门店。
3. 视需要在 `data/peers.json` 更新对标公司与估值。
4. 运行 `generate_report.py`，提交。报告即自动反映最新财报。

数据口径与来源见 [`data/sources.json`](data/sources.json)。
