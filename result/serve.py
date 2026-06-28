#!/usr/bin/env python3
"""
Standalone query server for gaokao admission databases.

Place this file alongside gaokao_*.db and toudang.db in any directory.
Uses only Python standard library — no dependencies.

Usage:
    cd result/
    python3 serve.py [--port 8765]

Then open http://localhost:8765
"""
import os
import sys
import json
import sqlite3
import argparse
import urllib.parse
import webbrowser
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
try:
    from http.server import ThreadingHTTPServer
except ImportError:
    ThreadingHTTPServer = None  # Python < 3.7 fallback
from pathlib import Path

# --- Discover databases relative to THIS script's location ---
HERE = Path(__file__).resolve().parent

# --- School province mapping ---
_SCHOOL_REVERSE = {}  # full → short
try:
    from school_province import get_province as _get_province_raw, SCHOOL_PROVINCE
except ImportError:
    import importlib.util
    spec = importlib.util.spec_from_file_location("school_province", HERE / "school_province.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _get_province_raw = mod.get_province
    SCHOOL_PROVINCE = mod.SCHOOL_PROVINCE


def get_province_robust(school_name):
    """Look up province, trying full name then short name via reverse lookup."""
    prov = _get_province_raw(school_name)
    if prov != "未知":
        return prov
    # Try reverse lookup: full → short → province
    short = _SCHOOL_REVERSE.get(school_name, school_name)
    if short != school_name:
        return _get_province_raw(short)
    # Try direct lookup in dict
    return SCHOOL_PROVINCE.get(school_name, "未知")


def find_databases():
    """Find all gaokao_*.db, toudang.db, and yiduan.db in the same directory as this script."""
    dbs = {}
    for f in sorted(HERE.glob("*.db")):
        name = f.stem
        if name.startswith("gaokao_"):
            year = int(name.split("_")[1])
            dbs[year] = str(f)
        elif name == "toudang":
            dbs["toudang"] = str(f)
        elif name == "yiduan":
            dbs["yiduan"] = str(f)
        elif name == "gaoxiaoinfo":
            dbs["gaoxiaoinfo"] = str(f)
        elif name == "xuekepinggu":
            dbs["xuekepinggu"] = str(f)
    return dbs


DBS = find_databases()
YEARS = sorted(k for k in DBS if isinstance(k, int))

# --- Simple in-memory cache with TTL (seconds) ---
import time as _time
_cache = {}
def _cached(key, fn, ttl=300):
    """Return cached result if fresh, otherwise call fn() and cache."""
    now = _time.time()
    if key in _cache:
        val, expires = _cache[key]
        if now < expires:
            return val
    val = fn()
    _cache[key] = (val, now + ttl)
    return val

def _invalidate_cache(prefix=""):
    """Invalidate cache entries whose key starts with prefix."""
    if prefix:
        keys = [k for k in _cache if k.startswith(prefix)]
    else:
        keys = list(_cache.keys())
    for k in keys:
        del _cache[k]

# --- School name resolution: short → full ---
_SCHOOL_FULL = {
    # Shanghai schools
    "复旦大学": "复旦大学", "上海交大": "上海交通大学", "同济大学": "同济大学",
    "华东师大": "华东师范大学", "华东理工": "华东理工大学", "东华大学": "东华大学",
    "上海财大": "上海财经大学", "上海外大": "上海外国语大学", "上海大学": "上海大学",
    "华东政法": "华东政法大学", "上经贸大": "上海对外经贸大学",
    "上海理工": "上海理工大学", "上海海事": "上海海事大学",
    "上海海大": "上海海洋大学", "上海中医": "上海中医药大学",
    "上海师大": "上海师范大学", "上海戏剧": "上海戏剧学院",
    "上海音乐": "上海音乐学院", "上海体大": "上海体育大学",
    "上海电力": "上海电力大学", "上工程": "上海工程技术大学",
    "上应大": "上海应用技术大学", "二工大": "上海第二工业大学",
    "上海政法": "上海政法学院", "立信金融": "上海立信会计金融学院",
    "上海电机": "上海电机学院", "上海商院": "上海商学院",
    "健康医学": "上海健康医学院", "海关学院": "上海海关学院",
    "上海杉达": "上海杉达学院", "建桥学院": "上海建桥学院",
    "中侨大学": "上海中侨职业技术大学", "立达学院": "上海立达学院",
    "上外贤达": "上海外国语大学贤达经济人文学院",
    "上师天华": "上海师范大学天华学院", "上海视觉": "上海视觉艺术学院",
    "兴伟学院": "上海兴伟学院",
    "复旦医学": "复旦大学上海医学院", "交大医学": "上海交通大学医学院",
    "海医大": "海军军医大学", "上财浙院": "上海财经大学浙江学院",
}


def resolve_school_name(short):
    """Resolve short school name to full name if known, otherwise return as-is."""
    return _SCHOOL_FULL.get(short, short)

# Build reverse mapping (full name → short name) for province lookup
for _short, _full in _SCHOOL_FULL.items():
    _SCHOOL_REVERSE[_full] = _short

def query_school_info(school_name=None):
    """Look up school metadata (985/211) by name. Returns all if no name given."""
    path = DBS.get("gaoxiaoinfo")
    if not path:
        return {}
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    if school_name:
        rows = conn.execute(
            "SELECT name, province, is_985, is_211, is_double_first_class FROM schools WHERE name = ?",
            (school_name,)
        ).fetchall()
        result = [dict(r) for r in rows]
    else:
        rows = conn.execute(
            "SELECT name, province, is_985, is_211, is_double_first_class FROM schools ORDER BY province, name"
        ).fetchall()
        result = [dict(r) for r in rows]
    conn.close()
    return result


# Cache school list and schemas
_school_cache = {}


def get_db(year):
    """Connect to a year's database."""
    path = DBS.get(year)
    if not path:
        return None
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def query_schools(year=None):
    """Get distinct school names, optionally for a specific year."""
    if year:
        conn = get_db(year)
        if not conn:
            return []
        rows = conn.execute(
            "SELECT DISTINCT school_name FROM admissions WHERE major_group_code != '' ORDER BY school_name"
        ).fetchall()
        conn.close()
        return [resolve_school_name(r["school_name"]) for r in rows]
    # Across all years
    schools = set()
    for y in YEARS:
        conn = get_db(y)
        if conn:
            rows = conn.execute(
                "SELECT DISTINCT school_name FROM admissions WHERE major_group_code != ''"
            ).fetchall()
            schools.update(resolve_school_name(r["school_name"]) for r in rows)
            conn.close()
    return sorted(schools)


def query_pivot(school=None, keyword=None, subject=None, province=None, score_min=None, score_max=None, rank_min=None, rank_max=None, years=None, limit=500):
    """
    Return pivoted data: each row is a (school, group_code, major_name),
    with columns for each year's min_score, avg_score, admission_count.
    """
    results = {}

    # Determine which years to query
    if years:
        query_years = [y for y in years if y in YEARS]
    else:
        query_years = YEARS

    for year in query_years:
        conn = get_db(year)
        if not conn:
            continue
        wheres = ["major_group_code != '' AND is_group_total = 0"]
        params = []
        if school:
            # Search both original short name and resolved full name
            expanded = []
            for short, full in _SCHOOL_FULL.items():
                if school in short or school in full:
                    expanded.append(short)
            if expanded:
                placeholders = ",".join(["?"] * len(expanded))
                wheres.append(f"school_name IN ({placeholders})")
                params.extend(expanded)
            else:
                wheres.append("school_name LIKE ?")
                params.append(f"%{school}%")
        if keyword:
            wheres.append("major_name LIKE ?")
            params.append(f"%{keyword}%")
        if subject:
            wheres.append("subject_requirement = ?")
            params.append(subject)

        sql = (
            "SELECT school_name, major_group_code, subject_requirement, "
            "major_group_name, major_name, admission_count, min_score, avg_score, "
            "min_rank, avg_rank "
            "FROM admissions WHERE " + " AND ".join(wheres) +
            " ORDER BY school_name, major_group_code, major_name"
        )

        rows = conn.execute(sql, params).fetchall()
        for r in rows:
            s_name = resolve_school_name(r["school_name"])
            # Use (school, major) as pivot key so same major stays on one row
            # even when major_group_code changes across years (e.g. 2025 code reassignment)
            key = (s_name, r["major_name"])
            if key not in results:
                results[key] = {
                    "school": resolve_school_name(r["school_name"]),
                    "province": get_province_robust(resolve_school_name(r["school_name"])),
                    "group_code": r["major_group_code"],
                    "subject": r["subject_requirement"],
                    "group_name": r["major_group_name"],
                    "major": r["major_name"],
                    "years": {},
                }
            else:
                # Update group_code/subject/group_name from latest year's data
                results[key]["group_code"] = r["major_group_code"]
                results[key]["subject"] = r["subject_requirement"] or results[key]["subject"]
                results[key]["group_name"] = r["major_group_name"] or results[key]["group_name"]
            results[key]["years"][year] = {
                "count": r["admission_count"],
                "min": r["min_score"],
                "avg": r["avg_score"],
                "min_rank": r["min_rank"],
                "avg_rank": r["avg_rank"],
            }
        conn.close()

    # Sort results
    sorted_keys = sorted(results.keys(), key=lambda k: (k[0], k[1]))
    output = [results[k] for k in sorted_keys]

    # Apply province filter
    if province:
        # Support both single string and list
        provinces = [province] if isinstance(province, str) else province
        output = [item for item in output if item.get("province") in provinces]

    # Apply score range filter
    if score_min is not None or score_max is not None:
        filtered = []
        for item in output:
            keep = True
            if score_min is not None or score_max is not None:
                has_match = False
                for y, data in item["years"].items():
                    try:
                        v = float(str(data["min"]).replace(">", "").replace("≥", ""))
                        if score_min is not None and v < score_min:
                            continue
                        if score_max is not None and v > score_max:
                            continue
                        has_match = True
                    except (ValueError, TypeError):
                        pass
                if score_min is not None or score_max is not None:
                    keep = has_match
            if keep:
                filtered.append(item)
        output = filtered

    # Apply rank range filter (on min_rank, skipping censored/missing ranks)
    if rank_min is not None or rank_max is not None:
        filtered = []
        for item in output:
            has_match = False
            for y, data in item["years"].items():
                rk_raw = data.get("min_rank")
                if rk_raw is None:
                    continue
                rk_str = str(rk_raw).strip()
                # Skip censored ranks (">2684") and non-numeric values
                if not rk_str or rk_str[0] in (">", "<", "前"):
                    continue
                try:
                    rk = int(float(rk_str))
                    if rank_min is not None and rk < rank_min:
                        continue
                    if rank_max is not None and rk > rank_max:
                        continue
                    has_match = True
                except (ValueError, TypeError):
                    pass
            if has_match:
                filtered.append(item)
        output = filtered

    return output[:limit]


def query_toudang(year=None):
    """Get toudang data."""
    path = DBS.get("toudang")
    if not path:
        return []
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    wheres = []
    params = []
    if year:
        wheres.append("year = ?")
        params.append(year)
    sql = "SELECT * FROM toudang"
    if wheres:
        sql += " WHERE " + " AND ".join(wheres)
    sql += " ORDER BY year, major_group_code"
    rows = conn.execute(sql, params).fetchall()
    result = [dict(r) for r in rows]
    # Add province
    for item in result:
        item["province"] = get_province_robust(item.get("school_name", ""))
    conn.close()
    return result


def query_yiduan():
    """Get pivoted score-rank data across all years."""
    path = DBS.get("yiduan")
    if not path:
        return {"years": [], "scores": []}
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row

    # Get years
    years = sorted(r["year"] for r in conn.execute(
        "SELECT DISTINCT year FROM yiduan ORDER BY year").fetchall())

    # Get all scores in descending order
    scores = sorted(set(r["score"] for r in conn.execute(
        "SELECT DISTINCT score FROM yiduan").fetchall()), reverse=True)

    # Build pivot: {score: {year: {count, cumulative}}}
    pivot = {}
    rows = conn.execute(
        "SELECT year, score, count, cumulative FROM yiduan ORDER BY score DESC").fetchall()
    for r in rows:
        s = r["score"]
        if s not in pivot:
            pivot[s] = {}
        pivot[s][r["year"]] = {"count": r["count"], "cumulative": r["cumulative"]}

    # Convert to ordered list
    result = []
    for s in scores:
        entry = {"score": s, "years": {}}
        for y in years:
            if y in pivot.get(s, {}):
                entry["years"][str(y)] = pivot[s][y]
        result.append(entry)

    conn.close()
    return {"years": years, "scores": result}


def query_rank(score):
    """Convert a score to rank (cumulative count) across all years."""
    path = DBS.get("yiduan")
    if not path:
        return {}
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row

    result = {}
    years = sorted(r["year"] for r in conn.execute(
        "SELECT DISTINCT year FROM yiduan ORDER BY year").fetchall())

    for y in years:
        # Find the row with the highest score <= query score
        row = conn.execute(
            "SELECT score, cumulative FROM yiduan WHERE year=? AND score >= ? "
            "ORDER BY score ASC LIMIT 1", (y, score)).fetchone()
        if row:
            result[str(y)] = {"score": row["score"], "rank": row["cumulative"]}

    conn.close()
    return result


def query_discipline_assessment(discipline=None, school=None):
    """Query 4th round national discipline assessment results."""
    path = DBS.get("xuekepinggu")
    if not path:
        return {"disciplines": [], "results": [], "categories": []}

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row

    # Get all disciplines for reference
    disc_rows = conn.execute(
        "SELECT code, name, category, category_en FROM disciplines ORDER BY category, code"
    ).fetchall()
    disciplines = [dict(r) for r in disc_rows]

    # Get categories
    cat_rows = conn.execute(
        "SELECT DISTINCT category FROM disciplines ORDER BY category"
    ).fetchall()
    categories = [r["category"] for r in cat_rows]

    # Query assessments
    results = []
    wheres = []
    params = []
    if discipline:
        # Match by discipline name (LIKE for partial match) or exact code
        wheres.append("(d.name LIKE ? OR d.code = ?)")
        params.extend([f"%{discipline}%", discipline])
    if school:
        wheres.append("a.school_name LIKE ?")
        params.append(f"%{school}%")

    sql = (
        "SELECT d.code, d.name as discipline_name, d.category, d.category_en, "
        "a.school_name, a.grade, a.rank_order "
        "FROM assessments a JOIN disciplines d ON a.discipline_code = d.code "
    )
    if wheres:
        sql += " WHERE " + " AND ".join(wheres)
    sql += " ORDER BY d.category, d.code, a.rank_order, a.school_name"
    rows = conn.execute(sql, params).fetchall()
    results = [dict(r) for r in rows]

    conn.close()
    return {"disciplines": disciplines, "results": results, "categories": categories}


def query_school_assessment_summary(school_name):
    """Get a school's discipline assessment summary (counts per grade)."""
    path = DBS.get("xuekepinggu")
    if not path:
        return {}

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row

    # Find the school
    school_row = conn.execute(
        "SELECT DISTINCT school_name FROM assessments WHERE school_name LIKE ? LIMIT 1",
        (f"%{school_name}%",)
    ).fetchone()
    if not school_row:
        conn.close()
        return {"found": False}

    matched_name = school_row["school_name"]

    # Grade counts
    grade_counts = {}
    for row in conn.execute(
        "SELECT grade, COUNT(*) as cnt FROM assessments "
        "WHERE school_name = ? GROUP BY grade ORDER BY rank_order",
        (matched_name,)
    ).fetchall():
        grade_counts[row["grade"]] = row["cnt"]

    # A+ disciplines
    aplus = conn.execute(
        "SELECT d.name as discipline_name, d.category FROM assessments a "
        "JOIN disciplines d ON a.discipline_code = d.code "
        "WHERE a.school_name = ? AND a.grade = 'A+' ORDER BY d.category",
        (matched_name,)
    ).fetchall()

    # All assessments with discipline info
    all_assessments = []
    for row in conn.execute(
        "SELECT d.code, d.name as discipline_name, d.category, a.grade, a.rank_order "
        "FROM assessments a JOIN disciplines d ON a.discipline_code = d.code "
        "WHERE a.school_name = ? ORDER BY a.rank_order, d.category",
        (matched_name,)
    ).fetchall():
        all_assessments.append(dict(row))

    conn.close()
    return {
        "found": True,
        "school_name": matched_name,
        "grade_counts": grade_counts,
        "aplus_disciplines": [dict(r) for r in aplus],
        "total_disciplines": len(all_assessments),
        "assessments": all_assessments,
    }


# --- HTTP Server ---
class GaokaoHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _send_html(self, path):
        full = HERE / path
        if full.exists():
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(full.read_bytes())
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        params = dict(urllib.parse.parse_qsl(parsed.query))

        # API routes
        if path == "/api/years":
            self._send_json(YEARS)

        elif path == "/api/schools":
            year = params.get("year")
            if year:
                year = int(year)
                self._send_json(query_schools(year))
            else:
                self._send_json(_cached("schools_all", lambda: query_schools(None)))

        elif path == "/api/query":
            school = params.get("school")
            keyword = params.get("keyword")
            subject = params.get("subject")
            province = params.get("province")
            score_min = params.get("score_min")
            score_max = params.get("score_max")
            rank_min = params.get("rank_min")
            rank_max = params.get("rank_max")
            limit = int(params.get("limit", 500))
            if score_min:
                score_min = float(score_min)
            if score_max:
                score_max = float(score_max)
            if rank_min:
                rank_min = int(rank_min)
            if rank_max:
                rank_max = int(rank_max)
            # Parse provinces (may be multiple via repeated param)
            province_raw = urllib.parse.parse_qs(parsed.query).get("province", [])
            provinces = None
            if len(province_raw) > 1:
                provinces = [p for p in province_raw if p]
            # Parse years (may be multiple via repeated param or comma-separated)
            years_raw = urllib.parse.parse_qs(parsed.query).get("years", [])
            years = None
            if years_raw:
                years_list = []
                for v in years_raw:
                    for part in v.split(","):
                        try:
                            years_list.append(int(part.strip()))
                        except ValueError:
                            pass
                if years_list:
                    years = years_list
            # Resolve province: None (no filter), str (single), or list (multi)
            prov_arg = provinces if provinces else (province or None)
            data = query_pivot(
                school=school,
                keyword=keyword,
                subject=subject,
                province=prov_arg,
                score_min=score_min,
                score_max=score_max,
                rank_min=rank_min,
                rank_max=rank_max,
                years=years,
                limit=limit,
            )
            out_years = sorted(years) if years else YEARS
            self._send_json({"years": out_years, "results": data, "count": len(data)})

        elif path == "/api/toudang":
            year = params.get("year")
            if year:
                year = int(year)
            self._send_json(query_toudang(year))

        elif path == "/api/stats":
            def _compute_stats():
                stats = {}
                for y in YEARS:
                    conn = get_db(y)
                    if conn:
                        r = conn.execute(
                            "SELECT COUNT(DISTINCT school_name) as schools, "
                            "COUNT(DISTINCT major_group_code) as groups, "
                            "COUNT(*) as majors "
                            "FROM admissions WHERE major_group_code != '' AND is_group_total = 0"
                        ).fetchone()
                        stats[str(y)] = {"schools": r["schools"], "groups": r["groups"], "majors": r["majors"]}
                        conn.close()
                return stats
            self._send_json(_cached("stats", _compute_stats))

        elif path == "/api/schoolinfo":
            school = params.get("school")
            if school:
                self._send_json(query_school_info(school))
            else:
                self._send_json(_cached("schoolinfo_all", lambda: query_school_info(None)))

        elif path == "/api/schools/autocomplete":
            q = params.get("q", "").strip()
            if not q or len(q) < 1:
                self._send_json([])
                return
            path_info = DBS.get("gaoxiaoinfo")
            if not path_info:
                self._send_json([])
                return
            conn = sqlite3.connect(path_info)
            conn.row_factory = sqlite3.Row
            # Match: name contains query (case-insensitive for ASCII, LIKE for CJK)
            try:
                rows = conn.execute(
                    "SELECT name, province, is_985, is_211, is_double_first_class FROM schools "
                    "WHERE name LIKE ? OR name LIKE ? "
                    "ORDER BY is_985 DESC, is_211 DESC, is_double_first_class DESC, name LIMIT 15",
                    (f"{q}%", f"%{q}%")
                ).fetchall()
            except sqlite3.OperationalError:
                # Fallback for old DB without is_double_first_class column
                rows = conn.execute(
                    "SELECT name, province, is_985, is_211, 0 as is_double_first_class FROM schools "
                    "WHERE name LIKE ? OR name LIKE ? "
                    "ORDER BY is_985 DESC, is_211 DESC, name LIMIT 15",
                    (f"{q}%", f"%{q}%")
                ).fetchall()
            result = [{
                "name": r["name"],
                "province": r["province"],
                "is_985": bool(r["is_985"]),
                "is_211": bool(r["is_211"]),
                "is_double_first_class": bool(r["is_double_first_class"]),
            } for r in rows]
            conn.close()
            self._send_json(result)

        elif path == "/api/majors/autocomplete":
            q = params.get("q", "").strip()
            if not q or len(q) < 1:
                self._send_json([])
                return
            # Search across all years for distinct major names
            results = set()
            for y in YEARS:
                conn = get_db(y)
                if conn:
                    rows = conn.execute(
                        "SELECT DISTINCT major_name FROM admissions "
                        "WHERE major_name != '' AND is_group_total=0 "
                        "AND (major_name LIKE ? OR major_name LIKE ?) "
                        "ORDER BY major_name LIMIT 10",
                        (f"{q}%", f"%{q}%")
                    ).fetchall()
                    results.update(r["major_name"] for r in rows)
                    conn.close()
            # Sort: exact prefix matches first, then contains
            pre = sorted([m for m in results if m.startswith(q)])
            rest = sorted([m for m in results if not m.startswith(q)])
            self._send_json((pre + rest)[:20])

        elif path == "/api/xueke/schools/autocomplete":
            q = params.get("q", "").strip()
            if not q or len(q) < 1:
                self._send_json([])
                return
            path_xk = DBS.get("xuekepinggu")
            if not path_xk:
                self._send_json([])
                return
            conn = sqlite3.connect(path_xk)
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT DISTINCT school_name FROM assessments "
                "WHERE school_name LIKE ? OR school_name LIKE ? "
                "ORDER BY school_name LIMIT 15",
                (f"{q}%", f"%{q}%")
            ).fetchall()
            result = [r["school_name"] for r in rows]
            conn.close()
            self._send_json(result)

        elif path == "/api/xueke/disciplines/autocomplete":
            q = params.get("q", "").strip()
            if not q or len(q) < 1:
                self._send_json([])
                return
            path_xk = DBS.get("xuekepinggu")
            if not path_xk:
                self._send_json([])
                return
            conn = sqlite3.connect(path_xk)
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT DISTINCT name FROM disciplines "
                "WHERE name LIKE ? OR name LIKE ? "
                "ORDER BY name LIMIT 15",
                (f"{q}%", f"%{q}%")
            ).fetchall()
            result = [r["name"] for r in rows]
            conn.close()
            self._send_json(result)

        elif path == "/api/subjects":
            def _compute_subjects():
                subjects = set()
                for y in YEARS:
                    conn = get_db(y)
                    if conn:
                        rows = conn.execute(
                            "SELECT DISTINCT subject_requirement FROM admissions "
                            "WHERE subject_requirement != '' AND major_group_code != ''"
                        ).fetchall()
                        subjects.update(r["subject_requirement"] for r in rows)
                        conn.close()
                return sorted(subjects)
            self._send_json(_cached("subjects", _compute_subjects))

        elif path == "/api/yiduan":
            self._send_json(query_yiduan())

        elif path == "/api/xueke":
            discipline = params.get("discipline", "").strip()
            school = params.get("school", "").strip()
            self._send_json(query_discipline_assessment(
                discipline=discipline or None,
                school=school or None
            ))

        elif path == "/api/xueke/school":
            school = params.get("school", "").strip()
            if school:
                self._send_json(query_school_assessment_summary(school))
            else:
                self._send_json({"error": "Missing school parameter"}, 400)

        elif path == "/api/xueke/categories":
            data = query_discipline_assessment()
            self._send_json(data.get("categories", []))

        elif path == "/api/provinces":
            from school_province import PROVINCES
            self._send_json(PROVINCES)

        elif path == "/api/rank":
            score = params.get("score")
            if score:
                self._send_json(query_rank(int(score)))
            else:
                self._send_json({"error": "Missing score parameter"}, 400)

        elif path == "" or path == "/":
            self._send_html("index.html")

        else:
            # Static file fallback
            file_path = HERE / path.lstrip("/")
            if file_path.exists() and file_path.suffix in (".html", ".css", ".js", ".png", ".ico", ".json"):
                self.send_response(200)
                ct = {"html": "text/html", "css": "text/css", "js": "application/javascript",
                      "png": "image/png", "ico": "image/x-icon", "json": "application/json"}.get(file_path.suffix[1:], "text/plain")
                self.send_header("Content-Type", f"{ct}; charset=utf-8")
                self.end_headers()
                self.wfile.write(file_path.read_bytes())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Not Found")


def main():
    parser = argparse.ArgumentParser(description="Gaokao DB Query Server")
    parser.add_argument("--port", type=int, default=8765, help="Port (default: 8765)")
    args = parser.parse_args()

    if not DBS:
        print("ERROR: No .db files found in", HERE)
        sys.exit(1)

    print(f"Found {len(YEARS)} year DBs: {YEARS}")
    if "toudang" in DBS:
        print(f"Found toudang.db")
    print(f"\nStarting server at http://localhost:{args.port}")
    print(f"Serving from: {HERE}")
    print(f"Press Ctrl+C to stop\n")

    # Use ThreadingHTTPServer for concurrent request handling (Python 3.7+)
    if ThreadingHTTPServer:
        server = ThreadingHTTPServer(("0.0.0.0", args.port), GaokaoHandler)
        print("Using threaded server (concurrent requests enabled)")
    else:
        server = HTTPServer(("0.0.0.0", args.port), GaokaoHandler)
        print("Using single-threaded server (upgrade to Python 3.7+ for concurrency)")

    # Auto-open browser after a short delay
    def open_browser():
        import time
        time.sleep(0.5)
        webbrowser.open(f"http://localhost:{args.port}")
    threading.Thread(target=open_browser, daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
