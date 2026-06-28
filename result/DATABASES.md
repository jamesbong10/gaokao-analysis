# 数据库说明

> 数据来源：上海市教育考试院发布的 2022–2025 年本科普通批次录取院校专业组扫描版 PDF，经多模态大模型 OCR 提取。

## 文件概览

| 文件 | 大小 | 内容 | 数据范围 |
|------|------|------|----------|
| `gaokao_2022.db` | 1.3 MB | 2022 年本科普通批录取详情 | ~4,400 行 / 4,369 专业明细 |
| `gaokao_2023.db` | 1.3 MB | 2023 年本科普通批录取详情 | ~4,400 行 / 4,407 专业明细 |
| `gaokao_2024.db` | 1.4 MB | 2024 年本科普通批录取详情 | ~4,700 行 / 4,719 专业明细 |
| `gaokao_2025.db` | 1.7 MB | 2025 年本科普通批录取详情 | ~5,000 行 / 5,045 专业明细 |
| `toudang.db` | 936 KB | 2020–2025 年投档线（官方） | 7,525 条 / 6 个年份 |
| `yiduan.db` | 86 KB | 2020–2026 年一分一段表 | 2,017 条 / 7 个年份 |
| `gaoxiaoinfo.db` | 56 KB | 高校信息库 | 744 所 / 39 所 985 / 118 所 211 |
| `xuekepinggu.db` | ~300 KB | 第四轮学科评估 | 95 个学科 / 5,112 条评估 / 463 所高校 |

---

## 录取数据库 `gaokao_20XX.db`

每个年份一个独立 SQLite 文件，结构相同。

### 表：`admissions`

存放专业级别的录取数据，每行代表一个院校专业组下的一个专业。

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `id` | INTEGER | 主键 | |
| `year` | INTEGER | 年份 | `2025` |
| `school_code` | TEXT | 3 位院校代码 | `102` |
| `school_name` | TEXT | 院校简称 | `上海交大` |
| `major_group_code` | TEXT | 5 位专业组代码（前 3 位=院校代码，后 2 位=组序号） | `10201` |
| `subject_requirement` | TEXT | 科目要求 | `物和化`、`不限`、`物` |
| `major_group_name` | TEXT | 专业组名称 | `上海交大(01)` |
| `major_name` | TEXT | 专业名称 | `人工智能(拔尖英才试点班)` |
| `admission_count` | INTEGER | 该专业录取人数 | `10` |
| `max_score` | TEXT | 最高分（被屏蔽时显示 `>580`） | `618` 或 `>580` |
| `min_score` | TEXT | 最低分 | `575` |
| `avg_score` | REAL | 平均分 | `585.5` |
| `min_rank` | TEXT | 最低分对应位次 | `2684` 或 `>2684`（屏蔽） |
| `avg_rank` | INTEGER | 平均分位次（仅有部分数据） | `2500` |
| `is_group_total` | INTEGER | 是否为专业组合计行（0=专业明细，1=组汇总） | `0` |
| `notes` | TEXT | 备注 | |
| `source_page` | INTEGER | 原始 PDF 页码 | `42` |
| `source_half` | TEXT | 半页位置（L=左，R=右） | `L` |
| `source_file` | TEXT | 来源 PDF 文件名 | |
| `ocr_confidence` | REAL | OCR 置信度 | `0.95` |

### 表：`schools`

存放院校代码与名称的映射。

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `code` | TEXT | 3 位院校代码（主键） | `102` |
| `name` | TEXT | 院校全称 | `上海交通大学` |
| `short_name` | TEXT | 院校简称 | `上海交大` |

### 表：`ocr_metadata`

存放 OCR 处理过程的元数据（键值对形式）。

### 分数屏蔽说明

高考成绩公布时，当年总成绩前若干名的考生分数被屏蔽（2022–2024 年为 580 分及以上，2025 年有所调整）。在 `max_score` 和 `min_score` 字段中，被屏蔽的分数以 `>580` 形式记录，`min_rank` 以 `>2684` 形式记录（"前 2684 名"）。

### 代码说明

- **普通专业组**（如 `10201`）：纯数字代码，前 3 位为院校代码，后 2 位为组序号
- **Q 组**（如 `102Q2`）：提前批 / 特殊类型招生专业组，投档线数据库不含此类

---

## 投档线数据库 `toudang.db`

基于上海市教育考试院每年发布的 `本科普通批投档线.pdf` 提取。

### 表：`toudang`

每行代表一个专业组的最低投档分数线（不含具体专业明细）。

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `id` | INTEGER | 主键 | |
| `year` | INTEGER | 年份 | `2025` |
| `major_group_code` | TEXT | 5 位专业组代码 | `10201` |
| `school_name` | TEXT | 院校简称 | `上海交大` |
| `group_number` | TEXT | 组序号 | `01` |
| `major_group_name` | TEXT | 院校专业组名称 | `上海交大(01)` |
| `min_score` | TEXT | 投档最低分（被屏蔽时为 `580分及以上`） | `575` |
| `is_censored` | INTEGER | 是否被屏蔽（1=是，0=否） | `0` |
| `min_rank` | REAL | 投档最低排名 | `2045` |
| `chinese_math` | REAL | 语文数学合计（最后一名投档考生） | `245` |
| `foreign_lang` | REAL | 外语成绩（最后一名投档考生） | `126` |
| `elective_best` | REAL | 选考最高科成绩 | `70` |
| `elective_second` | REAL | 选考次高科成绩 | `67` |
| `elective_third` | REAL | 选考最低科成绩 | `64` |
| `bonus_points` | REAL | 政策性加分 | `0` |
| `source_note` | TEXT | 数据来源备注 | |

**同分排序说明**：上海高考同分考生的排序规则依次比较：语文+数学合计 → 语文或数学单科最高 → 外语 → 选考最高 → 选考次高 → 选考最低。这些字段记录了最后一名投档考生的各科成绩，对压线判断至关重要。

**数据来源**：同分排序数据来自 [666keke/Shanghai-Gaokao](https://github.com/666keke/Shanghai-Gaokao) 项目的 `data.json`，合并匹配率 98.8%。

**约束**：`(year, major_group_code)` 唯一。

### 年份覆盖

| 年份 | 记录数 |
|------|--------|
| 2020 | 1,238 |
| 2021 | 1,246 |
| 2022 | 1,250 |
| 2023 | 1,248 |
| 2024 | 1,223 |
| 2025 | 1,320 |

### ⚠ 代码重编

2025 年上海市教育考试院重新分配了院校代码，同一三码前缀在不同年份可能代表不同院校。跨年对比时请以**院校名称**为准，不要依赖代码匹配。

---

## 一分一段数据库 `yiduan.db`

存放 2020–2026 年高考分数-位次对照表（一分一段表），用于分数与位次的互相转换。

### 表：`yiduan`

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `id` | INTEGER | 主键 | |
| `year` | INTEGER | 年份 | `2025` |
| `score` | INTEGER | 高考分数 | `580` |
| `count` | INTEGER | 该分数段人数 | `132` |
| `cumulative` | INTEGER | 累计人数（即全市排名） | `2684` |

**约束**：`(year, score)` 唯一。

### 年份覆盖

| 年份 | 记录数 | 分数范围 | 总考生数 | 数据来源 |
|------|--------|---------|----------|----------|
| 2020 | 352 | 611→260 | 44,940 | WPS 表格 PDF → pdftotext |
| 2021 | 336 | 615→280 | 44,086 | WPS 表格 PDF → pdftotext |
| 2022 | 340 | 619→280 | 44,839 | WPS 表格 PDF → pdftotext |
| 2023 | 336 | 619→284 | 51,560 | WPS 表格 PDF → pdftotext |
| 2024 | 217 | 619→403 | 41,594 | WPS 表格 PDF → pdftotext |
| 2025 | 222 | 623→402 | 49,276 | 扫描 PDF → kimi-k2.6 OCR |
| 2026 | 214 | 616→403 | 51,853 | 上海本地宝网页 HTML 解析 |

### 使用示例

```sql
-- 查询 580 分在各年的对应位次
SELECT year, score, cumulative FROM yiduan WHERE score = 580 ORDER BY year;

-- 查询位次 3000 在各年对应的大致分数
SELECT year, score, cumulative FROM yiduan
WHERE cumulative >= 3000 GROUP BY year ORDER BY year, cumulative ASC;

-- 对比各年同位次对应的分数变化
SELECT y1.year, y1.score, y2.score FROM yiduan y1
JOIN yiduan y2 ON y1.cumulative = y2.cumulative AND y1.year < y2.year
WHERE y1.year = 2020 AND y2.year = 2025 ORDER BY y1.score DESC LIMIT 20;
```

---

## 高校信息库 `gaoxiaoinfo.db`

存放院校的元数据：名称、所在省份、是否 985/211。

### 表：`schools`

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `id` | INTEGER | 主键 | |
| `name` | TEXT | 院校名称（唯一） | `上海交通大学` |
| `province` | TEXT | 所在省份 | `上海` |
| `is_985` | INTEGER | 是否 985（1=是，0=否） | `1` |
| `is_211` | INTEGER | 是否 211（1=是，0=否） | `1` |
| `is_double_first_class` | INTEGER | 是否双一流（1=是，0=否） | `1` |

**约束**：`name` 唯一。

### 统计

| 分类 | 数量 |
|------|------|
| 院校总数 | 744 |
| 985 高校 | 39 |
| 211 高校（含 985） | 118 |
| 双一流高校 | 86 |
| 覆盖省份 | 31 |

### 使用示例

```sql
-- 查看所有 985 高校
SELECT name, province FROM schools WHERE is_985 = 1 ORDER BY province;

-- 按省份统计院校数
SELECT province, COUNT(*) AS n FROM schools GROUP BY province ORDER BY n DESC;

-- 查看非 985/211 的双一流高校（如南方科大、上海科大等）
SELECT name, province FROM schools
WHERE is_double_first_class = 1 AND is_985 = 0 AND is_211 = 0;

-- 联合查询：找出 985 高校在某年的最低录取分
SELECT s.name, s.province, a.min_score
FROM schools s
JOIN gaokao_2025_admissions a ON a.school_name = s.name
WHERE s.is_985 = 1 AND a.is_group_total = 0
ORDER BY a.min_score DESC;
```

---

## 学科评估数据库 `xuekepinggu.db`

存放教育部学位与研究生教育发展中心（CDGDC）发布的**第四轮全国高校学科评估**结果（2017 年 12 月 28 日公布）。

### 评估分档

按"学科整体水平得分"的位次百分位，前 70% 的学科分 9 档公布：

| 档次 | 位次百分位 | 含义 |
|------|-----------|------|
| **A+** | 前 2%（或前 2 名） | 顶尖 |
| **A** | 2%～5% | 优秀 |
| **A-** | 5%～10% | 优秀 |
| **B+** | 10%～20% | 良好 |
| **B** | 20%～30% | 良好 |
| **B-** | 30%～40% | 良好 |
| **C+** | 40%～50% | 一般 |
| **C** | 50%～60% | 一般 |
| **C-** | 60%～70% | 一般 |

### 表：`disciplines`

存放 95 个一级学科信息。

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `code` | TEXT | 4 位学科代码（主键） | `0812` |
| `name` | TEXT | 一级学科名称 | `计算机科学与技术` |
| `category` | TEXT | 学科门类（中文） | `工学` |
| `category_en` | TEXT | 学科门类（英文） | `Engineering` |

### 表：`assessments`

存放高校在各学科的评估结果，共 5,112 条记录。

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `id` | INTEGER | 主键 | |
| `discipline_code` | TEXT | 学科代码（外键 → disciplines.code） | `0812` |
| `school_name` | TEXT | 高校全称 | `清华大学` |
| `grade` | TEXT | 评估档次 | `A+` |
| `rank_order` | INTEGER | 档次排序（1=A+ ~ 9=C-） | `1` |

### 统计

| 分类 | 数量 |
|------|------|
| 一级学科 | 95 |
| 学科门类 | 12（哲学/经济学/法学/教育学/文学/历史学/理学/工学/农学/医学/管理学/艺术学） |
| 评估记录 | 5,112 |
| 参评高校 | 463 |
| A+ 学科点 | 210 |
| A 类学科点（A+/A/A-） | 710 |

### 学科门类分布

| 门类 | 学科数 | 评估记录数 |
|------|--------|-----------|
| 工学 | 36 | 1,935 |
| 理学 | 14 | 708 |
| 管理学 | 5 | 459 |
| 医学 | 9 | 384 |
| 法学 | 5 | 381 |
| 文学 | 3 | 274 |
| 艺术学 | 5 | 249 |
| 农学 | 9 | 211 |
| 经济学 | 2 | 171 |
| 教育学 | 3 | 160 |
| 历史学 | 3 | 122 |
| 哲学 | 1 | 58 |

### 使用示例

```sql
-- 查询某高校所有学科评估结果
SELECT d.category, d.name AS discipline, a.grade
FROM assessments a
JOIN disciplines d ON a.discipline_code = d.code
WHERE a.school_name = '复旦大学'
ORDER BY a.rank_order, d.category;

-- 查询某学科所有高校评估结果
SELECT a.grade, a.school_name
FROM assessments a
WHERE a.discipline_code = '0812'  -- 计算机科学与技术
ORDER BY a.rank_order, a.school_name;

-- 统计各高校 A 类学科数量
SELECT school_name, COUNT(*) AS a_count
FROM assessments WHERE rank_order <= 3
GROUP BY school_name HAVING a_count >= 10
ORDER BY a_count DESC;

-- 按学科门类统计 A+ 高校
SELECT d.category, d.name AS discipline, a.school_name
FROM assessments a
JOIN disciplines d ON a.discipline_code = d.code
WHERE a.grade = 'A+'
ORDER BY d.category, d.name;

-- 联合高校信息库查询
SELECT s.name, s.province, s.is_985, COUNT(a.id) AS rated_disciplines,
       SUM(CASE WHEN a.rank_order <= 3 THEN 1 ELSE 0 END) AS a_level_count
FROM assessments a
JOIN gaoxiaoinfo_schools s ON s.name = a.school_name
GROUP BY s.name ORDER BY a_level_count DESC LIMIT 20;
```

### API 端点

| 端点 | 参数 | 说明 |
|------|------|------|
| `/api/xueke` | `school`, `discipline` | 查询评估结果（无参数返回全量） |
| `/api/xueke/school` | `school` | 查询某高校评估汇总（各档数量、A+ 学科列表） |
| `/api/xueke/schools/autocomplete` | `q` | 院校名称联想（从参评高校中搜索） |
| `/api/xueke/disciplines/autocomplete` | `q` | 学科名称联想（从 95 个一级学科中搜索） |
| `/api/xueke/categories` | — | 12 个学科门类列表 |

---

### 数据来源

- 教育部学位与研究生教育发展中心：https://www.cdgdc.edu.cn/dslxkpgjggb/
- GitHub 社区整理版：https://github.com/Johnnydaszhu/2017ChinaUniversityDisciplineAssessment
- 注意：第五轮学科评估（2022 年完成）未公开完整发布，本数据库收录的第四轮为最新可用的官方公开数据

---

## 通用 SQL 示例

```sql
-- 查询上海交大 2025 年所有专业录取数据
SELECT major_group_code, major_name, admission_count, min_score, avg_score
FROM admissions
WHERE year = 2025 AND school_name = '上海交大'
ORDER BY major_group_code, admission_count DESC;

-- 查询 2025 年"人工智能"相关专业在各校的录取分数
SELECT a.school_name, a.major_name, a.min_score, a.avg_score,
       t.min_score AS toudang_min
FROM admissions a
LEFT JOIN toudang t ON a.year = t.year AND a.major_group_code = t.major_group_code
WHERE a.year = 2025 AND a.is_group_total = 0 AND a.major_name LIKE '%人工智能%'
ORDER BY a.avg_score DESC;

-- 查询某专业组的最低分与投档线的差异
SELECT a.school_name, a.major_group_code,
       MIN(a.min_score) AS db_min, t.min_score AS td_min,
       CAST(REPLACE(MIN(a.min_score), '>', '') AS REAL) -
       CAST(REPLACE(t.min_score, '分及以上', '') AS REAL) AS diff
FROM admissions a
JOIN toudang t ON a.year = t.year AND a.major_group_code = t.major_group_code
WHERE a.year = 2025 AND NOT t.is_censored
GROUP BY a.major_group_code HAVING diff != 0
ORDER BY diff DESC;

-- 联合高校信息：按省份和 985/211 筛选
SELECT a.school_name, s.province, s.is_985, MIN(a.min_score) AS min
FROM admissions a
JOIN gaoxiaoinfo_schools s ON s.name = a.school_name
WHERE a.year = 2025 AND s.province = '上海' AND a.is_group_total = 0
GROUP BY a.school_name ORDER BY min DESC;
```

---

## 数据质量

| 年份 | 投档线匹配率 | 有效代码率 | min_rank 准确率 | avg_rank 准确率 | 数据来源 |
|------|-------------|-----------|----------------|----------------|----------|
| 2022 | 93.5% | 99.1% | 56.5% | 100% | 扫描 PDF → kimi-k2.6 OCR → 结构化解析 |
| 2023 | 96.6% | 99.1% | 66.0% | 99.5% | 同上 |
| 2024 | 96.3% | 99.1% | 96.2% | 97.2% | 同上 |
| 2025 | 97.4% | 99.1% | 98.1% | 98.6% | 同上 |

### 排名校准

OCR 提取的排名（`min_rank`、`avg_rank`）通过**一分一段表**（`yiduan.db`）交叉校核：

- 用一分一段表的分数→累计位次映射校验每条记录的分数-排位一致性
- 排名偏差超过 20% 或 500 名的标记为错误 → 清除 → 从一分一段表补全近似值
- 2022–2023 年 OCR 质量较差（存在列交换和截断），已修复约 3,400 行
- 2024–2025 年 OCR 质量较高，少量不匹配来自低于一分一段表覆盖范围的极低分段
- 被屏蔽分（`>580`）不补全排位，避免过度推测

### 投档线匹配

投档线不匹配主要集中在低分段院校（400 分以下），差异来源于投档线包含补录阶段数据，而录取数据 PDF 记载首次投档分数。

---

## 图表分析页面 `yiduan_analysis.html`

独立静态网页，展示 2020–2026 年一分一段表的 6 张分析图表，零外部依赖，可直接用浏览器打开。

**页面结构**（三栏导航）：

| 标签 | 图表 | 说明 |
|------|------|------|
| 总览 | 六合一总览图 + 关键数据卡片 | 考生总数 / 最高分 / 增幅 / ≥500 分占比 |
| 年度对比 | 考生总数对比、分数线位次走势、分段占比 | 跨年横向对比，志愿填报参考 |
| 分布形态 | 分数分布曲线、累计人数曲线、密度热力图 | 单年分数生态，深度分析 |

**交互功能**：
- 点击任意图表 → 全屏灯箱放大查看
- 顶部 sticky 导航，一键锚点跳转
- 响应式布局，手机/平板均可查看

**图表文件**（`charts/` 目录）：

| 文件 | 内容 |
|------|------|
| `01_total_students.png` | 各年考生总数对比 |
| `02_key_score_ranks.png` | 关键分数线（600/580/550/500/450）对应位次走势 |
| `03_score_tiers.png` | 高/中/低分段（≥580 / 500–579 / 450–499 / <450）占比 |
| `04_distribution_curve.png` | 分数-人数分布曲线（2024–2026） |
| `05_cumulative_curve.png` | 累计人数曲线 — 分数↔位次速查（2024–2026） |
| `06_heatmap.png` | 各年 × 分数段（10 分一档）人数密度热力图 |

---

## Excel 导出

| 文件 | 内容 | sheets |
|------|------|--------|
| `yiduan.xlsx` | 2020–2026 年一分一段表 | 汇总 + 7 个年份 sheet |

每个年份 sheet 含三列：分数（降序）、人数、累计人数，表头冻结，带格式边框。

---

## 处理流水线

| 步骤 | 脚本 | 说明 |
|------|------|------|
| 1 | `step1_convert.py` | PDF → 300 DPI PNG 图像 |
| 2 | `step2_vision_ocr.py` | 多模态 LLM OCR 逐半页提取结构化 JSON |
| 3 | `step3_reconstruct.py` | 记录组装、字段继承、去重校验 |
| 4 | `step5_export.py` | 导出 per-year SQLite |
| 5 | `step7_validate_toudang.py` | 与投档线对比验证 |
| — | `extract_yiduan.py` | 一分一段表 PDF 提取 |
| — | `build_gaoxiaoinfo.py` | 构建高校信息库 |
| — | `build_xuekepinggu.py` | 构建学科评估数据库 |
| — | `fix_avg_rank_swap.py` | 修复 OCR 列交换（均分↔排名） |
| — | `fix_rank_by_yiduan.py` | 用一分一段表校核并修复排位数据 |
| — | `fix_toudang_names.py` | 修复投档线 OCR 截断名称 |
| — | `fix_gaokao_names.py` | 用投档线名称校对录取库院校名 |
| — | `validate_by_yiduan.py` | 一分一段表交叉验证工具 |
| — | `merge_tongfen_data.py` | 合并 666keke 项目同分排序数据 |

流水线脚本位于 `../scripts/`。
