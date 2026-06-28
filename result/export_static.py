#!/usr/bin/env python3
"""Export all SQLite databases to static JSON for GitHub Pages deployment."""
import json, os, sys, sqlite3

os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.makedirs("data", exist_ok=True)

# ── Helpers ──
sys.path.insert(0, ".")
from serve import (
    query_pivot, query_toudang, query_yiduan, query_rank,
    query_school_info, query_discipline_assessment,
    find_databases, YEARS
)

def save(name, obj):
    path = os.path.join("data", name)
    json.dump(obj, open(path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    sz = os.path.getsize(path)
    print(f"  data/{name}: {sz:,} bytes ({sz/1024:.0f} KB)")

print("Exporting static data...\n")

# 1. Main pivot (compact keys to save space)
print("1. Pivot data (admissions)...")
full = query_pivot(limit=99999)
# Use full field names to minimize frontend changes
save("pivot.json", {"years": YEARS, "results": full})

# 2. Toudang
print("2. Toudang data...")
td = query_toudang()
save("toudang.json", td)

# 3. Yiduan
print("3. Yiduan data...")
yd = query_yiduan()
save("yiduan.json", yd)

# 4. Rank lookup (all scores 200-750)
print("4. Rank lookup...")
ranks = {}
for s in range(200, 751):
    ranks[str(s)] = query_rank(s)
save("ranks.json", ranks)

# 5. School info (all 747 schools)
print("5. School info...")
db = sqlite3.connect("gaoxiaoinfo.db")
all_schools = sorted(r[0] for r in db.execute("SELECT name FROM schools").fetchall())
db.close()
schoolinfo = {}
for s in all_schools:
    result = query_school_info(s)
    schoolinfo[s] = result[0] if result else {}
save("schoolinfo.json", schoolinfo)

# 6. Xueke
print("6. Xueke assessments...")
xk = query_discipline_assessment()
# Add school/discipline name lists for autocomplete
xk_schools = sorted(set(r["school_name"] for r in xk["results"]))
xk_disciplines = sorted(set(r["discipline_name"] for r in xk["results"]))
xk["schools"] = xk_schools
xk["disciplines"] = xk_disciplines
save("xueke.json", xk)

# 7. Reference lists (subjects, provinces, autocomplete indexes)
print("7. Reference lists...")
# Subjects
subjects = set()
for r in full:
    if r["subject"]:
        subjects.add(r["subject"])
subjects = sorted(subjects)

# Provinces
provinces = sorted(set(r["province"] for r in full if r["province"]))

# School names for autocomplete (with priority info)
school_names = sorted(set(r["school"] for r in full))

# Major names for autocomplete
majors_map = {}
for r in full:
    m = r["major"]
    if m:
        # Index by first character for prefix search
        prefix = m[0]
        if prefix not in majors_map:
            majors_map[prefix] = set()
        majors_map[prefix].add(m)
# Convert sets to sorted lists
majors_index = {k: sorted(v) for k, v in majors_map.items()}

# Stats
stats = {}
for y in YEARS:
    yr_data = [r for r in full if y in r["years"]]
    schools = set(r["school"] for r in yr_data)
    stats[str(y)] = {"schools": len(schools), "majors": len(yr_data)}

lists = {
    "subjects": subjects,
    "provinces": provinces,
    "schools": school_names,
    "majors_index": majors_index,
    "stats": stats,
}
save("lists.json", lists)

# Summary
total = sum(os.path.getsize(os.path.join("data", f)) for f in os.listdir("data"))
print(f"\n{'='*50}")
print(f"Total: {total:,} bytes ({total/1024/1024:.1f} MB)")
print("Done! Ready for static deployment.")
