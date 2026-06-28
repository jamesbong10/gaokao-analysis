# 上海高考录取数据查询工具

自包含、免安装的本地网页查询工具。复制 `result/` 文件夹到任意电脑即可运行。

## 包含数据

| 数据库 | 内容 | 年份 |
|--------|------|------|
| `gaokao_2022.db` | 本科普通批录取详情（院校/专业组/专业/分数/位次） | 2022 |
| `gaokao_2023.db` | 同上 | 2023 |
| `gaokao_2024.db` | 同上 | 2024 |
| `gaokao_2025.db` | 同上 | 2025 |
| `toudang.db` | 本科普通批投档线 | 2020–2025 |
| `yiduan.db` | 一分一段表（分数-位次对照） | 2020–2026 |
| `yiduan.xlsx` | 一分一段表 Excel 导出（每年一个 sheet） | 2020–2026 |
| `gaoxiaoinfo.db` | 高校信息（省份、985/211） | 744 所院校 |
| `xuekepinggu.db` | 第四轮学科评估（A+ ~ C-） | 95 个学科 / 5,112 条记录 |

## 运行方法

### 前置条件

- **Python 3**（macOS / Linux 自带；Windows 需安装，勾选 "Add Python to PATH"）

### 一键启动（推荐）

| 系统 | 文件 | 操作 |
|------|------|------|
| macOS | `start.command` | 双击即可 |
| Windows | `start.bat` | 双击即可 |

> 双击后会自动打开浏览器。如果 macOS 提示"无法打开"，右键 → 打开即可。

### 命令行启动

#### macOS / Linux

```bash
cd result/
python3 serve.py
```

#### Windows

```bash
cd result
python serve.py
```

> 如果提示找不到 python，换成 `py serve.py`

### 启动后

浏览器会自动打开 `http://localhost:8765`。如果没有自动打开，手动访问该地址。

## 界面说明

右上角四个 tab 按钮切换数据视图：

| 按钮 | 功能 |
|------|------|
| **录取数据** | 按院校/省份/专业/科目/分数筛选，查看各专业历年录取详情 |
| **投档线** | 查看各院校专业组的投档最低分（2020–2025） |
| **一分一段** | 查看各分数段人数和累计排名，支持输入分数查位次 |
| **学科评估** | 按院校或学科查询第四轮学科评估结果（A+ ~ C-） |

- 录取数据视图可按**院校名称、省份、专业关键词、科目要求、分数范围**筛选
- 院校名旁自动显示 `985` `211` `双` 角标（红=985，蓝=211，紫=双一流）
- 院校、专业、学科输入框均支持**输入联想**（自动补全）
- 点击列标题可按该列排序（▲ 升序 / ▼ 降序）
- 一分一段视图可输入分数，查询在各年对应的全市排名
- 投档线视图按院校名称排序，2025 年列高亮提示代码重编，**悬停可查看同分排序明细**（语数合计、外语、选考成绩）
- 学科评估视图默认全量显示 95 个学科评估结果，可按院校/学科/门类筛选

## 自定义端口

```bash
python3 serve.py --port 8080
```

## 文件说明

```
result/
├── start.command         ← macOS 一键启动（双击）
├── start.bat             ← Windows 一键启动（双击）
├── serve.py              ← 后端服务（纯 Python 标准库，无外部依赖）
├── index.html            ← 前端页面
├── school_province.py    ← 院校→省份映射表
├── gaokao_20XX.db        ← 录取数据库（4 个年份）
├── toudang.db            ← 投档线数据库（2020–2025）
├── yiduan.db             ← 一分一段数据库（2020–2026）
├── yiduan.xlsx            ← 一分一段表 Excel（每年一个 sheet）
├── yiduan_analysis.html   ← 一分一段表图表分析页面
├── yiduan_charts_combined.png ← 六合一图表总览
├── charts/                ← 6 张独立分析图表
│   ├── 01_total_students.png
│   ├── 02_key_score_ranks.png
│   ├── 03_score_tiers.png
│   ├── 04_distribution_curve.png
│   ├── 05_cumulative_curve.png
│   └── 06_heatmap.png
├── gaoxiaoinfo.db        ← 高校信息库（省份 / 985 / 211）
├── xuekepinggu.db        ← 第四轮学科评估结果
├── DATABASES.md          ← 数据库字段说明
└── README.md             ← 本文件
```
