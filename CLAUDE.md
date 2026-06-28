# 上海高考录取数据查询工具 — 项目详情

> 本文档供 AI 智能体（Claude Code）在后续会话中恢复项目上下文。
> 每次重大变更后应更新此文件。

## 项目概述

自包含、零外部依赖的本地网页查询工具，用于查询上海高考（2022–2025）本科普通批次录取数据。复制 `result/` 文件夹到任意安装 Python 3 的电脑即可运行。

**启动方式**：
```bash
cd result/
python3 serve.py            # → http://localhost:8765
# 或双击 start.command (macOS) / start.bat (Windows)
```

---

## 数据库清单（8 个，均位于 `result/`）

### 1. `gaokao_20XX.db`（4 个，2022–2025）
**来源**：上海市教育考试院发布的本科普通批次录取院校专业组扫描版 PDF → 多模态大模型（kimi-k2.6）OCR 提取。

**表 `admissions`**：专业级录取数据，`is_group_total=0` 为专业明细。
| 关键字段 | 说明 |
|----------|------|
| `school_name` | 院校简称（如"上海交大"） |
| `major_group_code` | 5 位专业组代码 |
| `major_name` | 专业名称 |
| `min_score`, `avg_score` | 最低分/平均分 |
| `min_rank`, `avg_rank` | 最低分位次/平均分位次（部分从一分一段表补全） |
| `admission_count` | 录取人数 |
| `subject_requirement` | 科目要求（如"物和化"） |

**表 `schools`**：院校代码↔名称映射。**表 `ocr_metadata`**：OCR 处理元数据。

**⚠ 分数屏蔽**：2022–2024 年 ≥580 分的成绩被屏蔽，记录为 `>580`。此类行的 `min_rank` 字段保持 NULL（不做推测）。

### 2. `toudang.db`
**来源**：本科普通批投档线 PDF（文字版）提取 + [666keke/Shanghai-Gaokao](https://github.com/666keke/Shanghai-Gaokao) 同分排序数据合并。

**表 `toudang`**（8,147 条，2020–2025）：
| 关键字段 | 说明 |
|----------|------|
| `min_score` | 投档最低分 |
| `min_rank` | 投档最低排名（99% 覆盖） |
| `chinese_math` | 语文+数学合计（最后一名投档考生） |
| `foreign_lang` | 外语成绩 |
| `elective_best/second/third` | 选考各科成绩 |
| `bonus_points` | 政策性加分 |
| `source_note` | `"imported_from_666keke"` 表示该记录来自外部数据源 |

**⚠ 2025 代码重编**：上海市教育考试院在 2025 年重新分配了所有 3 位院校代码，跨年对比须以院校名称为准。

### 3. `yiduan.db`
**来源**：2020–2025 年一分一段表，2020–2024 来自 WPS 文字 PDF（pdftotext -raw），2025 来自扫描 PDF（kimi-k2.6 OCR）。2026 年数据来自上海本地宝网页 HTML 解析。

**表 `yiduan`**（共 2,017 条）：`year, score, count（该分数人数）, cumulative（累计排名）`。

**用途**：分数↔位次互相转换；校核 gaokao_*.db 中 OCR 提取的排名数据。

### 3b. 图表分析页面 & Excel 导出
- `yiduan_analysis.html` — 独立静态网页，6 张分析图表 + lightbox + 三栏导航
- `yiduan.xlsx` — 一分一段表 Excel（汇总 sheet + 7 个年份 sheet，带格式）
- `yiduan_charts_combined.png` — 六合一总览图
- `charts/` — 6 张独立 PNG 图表

### 4. `gaoxiaoinfo.db`
**来源**：手动整理 + `scripts/build_gaoxiaoinfo.py` 构建 + `scripts/add_shuangyiliu.py` 补充双一流标识。

**表 `schools`**（747 所）：
| 字段 | 说明 |
|------|------|
| `name` | 院校全称（UNIQUE） |
| `province` | 所在省份（31 省） |
| `is_985` | 985（39 所） |
| `is_211` | 211（118 所含 985） |
| `is_double_first_class` | 双一流（第二轮 2022 发布，147 所，DB 中有 86 所可匹配） |

**注意**：南方科技大学、上海科技大学、中国科学院大学为非 985/211 的双一流新增校，手动补入。

### 5. `xuekepinggu.db`
**来源**：教育部学位中心第四轮学科评估（2017 年发布），从 GitHub 社区 CSV 导入（`scripts/build_xuekepinggu.py`）。

**表 `disciplines`**（95 个一级学科）：`code, name, category, category_en`。
**表 `assessments`**（5,112 条）：`discipline_code, school_name, grade（A+~C-）, rank_order（1~9）`。

**注意**：第五轮学科评估未公开完整发布，第四轮为最新可用官方数据。

---

## 服务端架构（`result/serve.py`）

纯 Python 标准库 HTTP 服务器（`http.server`），**零外部依赖**。

### 数据解析层
- `school_province.py`：院校名→省份映射表，含 `_SCHOOL_FULL`（简称→全名）和 `_SCHOOL_REVERSE`（全名→简称）双向映射
- 查询链路自动解析简称→全名→省份
- 院校名联想从 `gaoxiaoinfo.db` 查询，专业名联想从所有年份 `admissions` 表聚合

### API 端点（17 个）

| 端点 | 参数 | 用途 |
|------|------|------|
| `/api/years` | — | 可用年份列表 |
| `/api/query` | school, keyword, subject, province, score_min, score_max | **主查询**：录取数据 pivot（支持多维筛选） |
| `/api/toudang` | year | 投档线数据（含同分排序） |
| `/api/yiduan` | — | 一分一段全量 |
| `/api/rank` | score | 分数查位次 |
| `/api/stats` | — | 各年统计 |
| `/api/schools` | year | 院校列表 |
| `/api/provinces` | — | 省份列表 |
| `/api/subjects` | — | 科目要求列表 |
| `/api/schoolinfo` | school | 院校元数据（985/211/双一流） |
| `/api/schools/autocomplete` | q | 院校名联想（985/211/双一流优先） |
| `/api/majors/autocomplete` | q | 专业名联想（前缀优先） |
| `/api/xueke` | school, discipline | 学科评估查询（无参数返回全量） |
| `/api/xueke/school` | school | 某校评估汇总 |
| `/api/xueke/categories` | — | 12 个学科门类 |
| `/api/xueke/schools/autocomplete` | q | 学科评估院校联想 |
| `/api/xueke/disciplines/autocomplete` | q | 学科名称联想 |

---

## 前端架构（`result/index.html`）

单文件 HTML（约 37 KB），内联 CSS + JS，零外部依赖。

### 四个 Tab 视图

| Tab | 功能 | 特殊功能 |
|-----|------|---------|
| **录取数据** | 按条件筛选专业级录取详情，4 年数据 pivot | 默认按最新年分数降序；点击列头排序 |
| **投档线** | 院校专业组投档分，6 年数据 | 悬停显示同分排序明细；排名在分数下方 |
| **一分一段** | 分数段人数+累计排名 | 输入分数实时查位次 |
| **学科评估** | 全量/按条件查询第四轮学科评估 | 按院校显示学科档次；按学科分 A/B/C 三栏 |

### 关键设计决策
- 默认排序：`getBestYearVal()` 从 2025→2022 找第一个非零 min_score 降序排列
- 院校名 badge 优先级：985（红）> 211（蓝）> 双一流非 985/211（紫"双"）
- 页面打开自动加载录取数据（`init()` 末尾调用 `search()`）
- 投档线视图 2025 年列黄色高亮（代码重编警告）
- 学科评估视图进入自动全量加载（`loadXuekeInit()` → `xuekeSearch()`）

---

## 数据处理流水线

### 主流水线（PDF OCR）
| 步骤 | 脚本 | 说明 |
|------|------|------|
| 1 | `step1_convert.py` | PDF → 300 DPI PNG |
| 2 | `step2_vision_ocr.py` | 多模态 LLM 逐半页提取 JSON |
| 3 | `step3_reconstruct.py` | 记录组装、字段继承、去重 |
| 4 | `step5_export.py` | 导出 per-year SQLite |
| 5 | `step7_validate_toudang.py` | 与投档线对比验证 |

### 数据质量修复
| 脚本 | 说明 | 修复量 |
|------|------|--------|
| `fix_avg_rank_swap.py` | 修复 OCR 列交换：`avg_score` ↔ `avg_rank` | 2022: 678 行, 2023: 681 行 |
| `fix_avg_rank_swap2.py` | 第二轮修复：`min_rank ≈ min_score` 模式检测 | 2023: 48 行 |
| `fix_rank_by_yiduan.py` | 用一分一段表校核排名：NULL 错误值 + 补全缺失值 | 共 3,419 行 min_rank + 16,377 行 avg_rank |
| `fix_toudang_names.py` | 修复投档线 OCR 截断校名 | |
| `fix_gaokao_names.py` | 用 toudang 校名校对 gaokao 库校名 | 551 行 |
| `validate_by_yiduan.py` | 一分一段表交叉验证工具（只读） | |

### 外部数据导入
| 脚本 | 说明 |
|------|------|
| `merge_tongfen_data.py` | 合并 666keke 项目的同分排序数据到 toudang.db（7,432 条） |
| `import_missing_groups.py` | 从 666keke 导入我们缺失的本科普通批专业组（622 条） |
| `build_xuekepinggu.py` | 从 GitHub CSV 构建学科评估数据库 |
| `build_gaoxiaoinfo.py` | 构建高校信息库 |
| `add_shuangyiliu.py` | 补充双一流标识（增 3 所缺失校） |
| `extract_yiduan.py` | 一分一段表 PDF 提取 |

---

## 已知问题/注意事项

1. **2025 代码重编**：3 位院校代码在 2025 年全部重新分配，跨年必须用校名匹配
2. **北京师范大学缺失**：该校在所有数据库中都不存在（toudang、gaokao_*、gaoxiaoinfo），是已知数据空白
3. **分数屏蔽**：`>580` 的 `min_rank` 保持 NULL（不推测），`avg_score` 正常（未被屏蔽）
4. **低分段排名**：2024 年一分一段表最低分 403，2025 年最低 402，低于此分数的排名无法从一分一段表验证
5. **投档线 ≠ 录取线**：投档线（toudang）可能是补录后的分数，与录取数据（gaokao_*）的首次投档分数有差异
6. **OCR 质量**：2024–2025 年准确率 96–98%，2022–2023 年准确率约 57–66%（排名经一分一段表修复）
7. **双一流覆盖**：`gaoxiaoinfo.db` 中双一流仅 86 所可匹配，完整 147 所需重建数据库
8. **2026 一分一段数据来源**：2026 年数据来自第三方网站（上海本地宝）HTML 解析，非官方 PDF 提取，待官方发布后应核实

---

## 相关外部项目

| 项目 | 用途 | 数据复用 |
|------|------|---------|
| [666keke/Shanghai-Gaokao](https://github.com/666keke/Shanghai-Gaokao) | Next.js 志愿分析工作台 | 同分排序数据 + 缺失专业组（98.8% 匹配合并） |
| [MWang-TS/gaokaoapply](https://github.com/MWang-TS/gaokaoapply) | Tauri 桌面应用 + AI 对话 | `zhangxuefeng.md` Skill、专业富数据（学费/学制）可借鉴 |
| [Johnnydaszhu/2017ChinaUniversityDisciplineAssessment](https://github.com/Johnnydaszhu/2017ChinaUniversityDisciplineAssessment) | 第四轮学科评估 CSV | 直接导入构建 `xuekepinggu.db` |

---

## 修改指南

### 添加新数据源
1. 写脚本放在 `scripts/`
2. 输出到 `result/` 或更新已有 `.db`
3. 在 `serve.py` 添加 API 端点（如需要）
4. 在 `index.html` 添加对应的 Tab/视图（如需要）
5. 更新 `DATABASES.md` 和本文件

### 数据兼容性
- 所有 `.db` 文件必须在 `result/` 目录，`serve.py` 自动发现
- `gaokao_*.db` 命名规则：`gaokao_<四位年份>.db`
- `toudang.db` 的 `(year, major_group_code)` 唯一约束
- `gaoxiaoinfo.db` 的 `schools.name` 唯一约束
- 校名统一使用简称（如"上海交大"），通过 `school_province.py` 映射全名

### 端口管理
```bash
lsof -ti:8765 | xargs kill -9   # 停止旧服务器
python3 serve.py --port 8765     # 启动
```
