"""
=============================================================
  KURIGRAM DASHBOARD UPDATER v6 — All 5 disaster types
  Run: python update_dashboard.py
  Then drag HTML to Netlify Deploys tab
=============================================================
"""
import requests, json, sys, os, re
from datetime import datetime

API_TOKEN = "47f1457c09e523c388ec399f53abac0c44b0a0f1"
ASSET_UID = "avF5RDb7CE4bDugRdwuBwS"
SERVER    = "kf.kobotoolbox.org"
OUTPUT = "index.html"

# ── 100% CONFIRMED field names from fields_all.txt ──────────

# Location
F_UZ   = "location/uz"
F_UP   = "location/up"
F_DATE = "_submission_time"
F_DES  = "des_typ"
F_GEO  = "__003"          # geopoint: "lat lon alt acc"
F_NEED = "__006"          # current needs
F_RESP = "__007"          # respondent name

# Rainfall (prefix: rainfall/)
R = {
    "villages":   "rainfall/rain_villages",
    "agri":       "rainfall/rain_agri_land",
    "homes":      "rainfall/rain_hh_loss",
    "trees":      "rainfall/rain_tree",
    "road_pts":   "rainfall/rain_road_pts",
    "fish_pts":   "rainfall/rain_fish_pts",
    "displaced":  "rainfall/rain_job_displaced",
    "erosion_pts":"rainfall/rain_river_erosion_pts",
}

# Heatwave (prefix: heat/)
H = {
    "days":       "heat/heat_days",
    "avg_temp":   "heat/heat_avg_temp",
    "sick":       "heat/heat_sick_people",
    "treated":    "heat/heat_treated",
    "livestock":  "heat/heat_livestock_death",
    "poultry":    "heat/heat_poultry_death",
    "agri":       "heat/heat_agri_land",
    "agri_hh":    "heat/heat_agri_hh",
    "schools":    "heat/heat_school_closed",
    "displaced":  "heat/heat_displaced",
}

# Cold wave (prefix: cold/)
C = {
    "days":       "cold/cold_days",
    "avg_temp":   "cold/cold_avg_temp",
    "sick":       "cold/cold_sick_people",
    "treated":    "cold/cold_treated",
    "livestock":  "cold/cold_livestock_death",
    "poultry":    "cold/cold_poultry_death",
    "agri":       "cold/cold_agri_land",
    "schools":    "cold/cold_school_closed",
}

# Drought (prefix: drought/)
D = {
    "days":       "drought/drought_days",
    "avg_temp":   "drought/drought_avg_temp",
    "agri":       "drought/drought_agri_land",
    "treated":    "drought/drought_treated",
    "livestock":  "drought/drought_livestock_death",
    "poultry":    "drought/drought_poultry_death",
    "schools":    "drought/drought_school_closed",
    "displaced":  "drought/drought_displaced",
    "erosion_pts":"drought/drought_riverbank_pts",
}

# Flood (prefix: flood/)
FL = {
    "villages":   "flood/flood_villages",
    "homes":      "flood/flood_house_damaged",
    "waterlogged":"flood/flood_waterlogged_hh",
    "shelter_hh": "flood/flood_shelter_hh",
    "shelter_cap":"flood/flood_shelter_capacity",
    "road_pts":   "flood/flood_road_pts",
    "agri":       "flood/flood_agri_land",
    "schools":    "flood/flood_school_closed",
    "treated":    "flood/flood_treated",
    "deaths":     "flood/flood_drowning_deaths",
    "fish_pts":   "flood/flood_fish_pts",
    "displaced":  "flood/flood_displaced",
    "erosion_pts":"flood/flood_riverbank_pts",
}

UZ_MAP = {
    "uz_1":"Kurigram Sadar","uz_2":"Ulipur","uz_3":"Chilmari",
    "uz_4":"Nageshwari","uz_5":"Bhurungamari","uz_6":"Rowmari",
}
DES_CODES = {
    "des_1":"Rainfall","des_2":"Heatwave","des_3":"Cold Wave",
    "des_4":"Drought","des_5":"Flood",
    # also handle word-based codes from newer submissions
    "rain":"Rainfall","heat":"Heatwave","cold":"Cold Wave",
    "drought":"Drought","flood":"Flood",
}

def nv(r, key):
    try: return float(r.get(key, 0) or 0)
    except: return 0

def decode_disaster(raw):
    if not raw: return "Unknown"
    parts = str(raw).strip().split()
    names = []
    for p in parts:
        if p in DES_CODES and DES_CODES[p] not in names:
            names.append(DES_CODES[p])
    return ", ".join(names) if names else raw

def fetch():
    print("\n" + "="*50)
    print("  KURIGRAM DASHBOARD UPDATER v6")
    print("="*50)
    print("\n🔗 Fetching from KoboToolbox...")
    url = f"https://{SERVER}/api/v2/assets/{ASSET_UID}/data/?format=json&limit=30000"
    r = requests.get(url, headers={"Authorization": f"Token {API_TOKEN}"}, timeout=60)
    if r.status_code != 200:
        print(f"❌ Error {r.status_code}: {r.text[:200]}"); sys.exit(1)
    results = r.json().get("results", [])
    print(f"✅ {len(results)} submissions fetched")
    return results

def process(results):
    rows = []
    for r in results:
        uz_code  = str(r.get(F_UZ, '') or '')
        des_raw  = str(r.get(F_DES, '') or '')
        des_name = decode_disaster(des_raw)

        # Parse geopoint "__003" = "lat lon alt acc"
        geo = str(r.get(F_GEO, '') or '')
        lat, lon = None, None
        if geo and geo not in ('', 'None'):
            parts = geo.split()
            try: lat, lon = float(parts[0]), float(parts[1])
            except: pass

        row = {
            "upazila":   UZ_MAP.get(uz_code, uz_code) or 'Unknown',
            "union":     str(r.get(F_UP, '') or ''),
            "date":      str(r.get(F_DATE, '') or '')[:10],
            "disaster":  des_name,
            "des_raw":   des_raw,
            "lat":       lat,
            "lon":       lon,
            "needs":     str(r.get(F_NEED, '') or '')[:80],
            "respondent":str(r.get(F_RESP, '') or ''),

            # Rainfall
            "rain_villages":  int(nv(r, R["villages"])),
            "rain_agri":      nv(r, R["agri"]),
            "rain_homes":     int(nv(r, R["homes"])),
            "rain_displaced": int(nv(r, R["displaced"])),
            "rain_road_pts":  int(nv(r, R["road_pts"])),

            # Heatwave
            "heat_days":      int(nv(r, H["days"])),
            "heat_temp":      nv(r, H["avg_temp"]),
            "heat_sick":      int(nv(r, H["sick"])),
            "heat_treated":   int(nv(r, H["treated"])),
            "heat_livestock": int(nv(r, H["livestock"])),
            "heat_poultry":   int(nv(r, H["poultry"])),
            "heat_agri":      nv(r, H["agri"]),
            "heat_schools":   int(nv(r, H["schools"])),
            "heat_displaced": int(nv(r, H["displaced"])),

            # Cold wave
            "cold_days":      int(nv(r, C["days"])),
            "cold_temp":      nv(r, C["avg_temp"]),
            "cold_sick":      int(nv(r, C["sick"])),
            "cold_treated":   int(nv(r, C["treated"])),
            "cold_livestock": int(nv(r, C["livestock"])),
            "cold_agri":      nv(r, C["agri"]),
            "cold_schools":   int(nv(r, C["schools"])),

            # Drought
            "drought_days":      int(nv(r, D["days"])),
            "drought_agri":      nv(r, D["agri"]),
            "drought_treated":   int(nv(r, D["treated"])),
            "drought_livestock": int(nv(r, D["livestock"])),
            "drought_schools":   int(nv(r, D["schools"])),
            "drought_displaced": int(nv(r, D["displaced"])),

            # Flood
            "flood_villages":  int(nv(r, FL["villages"])),
            "flood_homes":     int(nv(r, FL["homes"])),
            "flood_agri":      nv(r, FL["agri"]),
            "flood_schools":   int(nv(r, FL["schools"])),
            "flood_treated":   int(nv(r, FL["treated"])),
            "flood_deaths":    int(nv(r, FL["deaths"])),
            "flood_displaced": int(nv(r, FL["displaced"])),
            "flood_waterlogged":int(nv(r, FL["waterlogged"])),
            "flood_shelter_hh": int(nv(r, FL["shelter_hh"])),
        }

        # Computed totals per row
        row["homes"]     = row["rain_homes"] + row["flood_homes"]
        row["agri"]      = row["rain_agri"] + row["heat_agri"] + row["cold_agri"] + row["drought_agri"] + row["flood_agri"]
        row["schools"]   = row["heat_schools"] + row["cold_schools"] + row["drought_schools"] + row["flood_schools"]
        row["treated"]   = row["heat_treated"] + row["cold_treated"] + row["drought_treated"] + row["flood_treated"]
        row["deaths"]    = row["flood_deaths"]
        row["livestock"] = row["heat_livestock"] + row["cold_livestock"] + row["drought_livestock"]
        row["displaced"] = row["rain_displaced"] + row["heat_displaced"] + row["drought_displaced"] + row["flood_displaced"]

        rows.append(row)

    def sm(k): return sum(r[k] for r in rows)

    kpis = {
        "submissions": len(rows),
        "homes":       sm("homes"),
        "agri":        round(sm("agri"), 1),
        "schools":     sm("schools"),
        "deaths":      sm("deaths"),
        "treated":     sm("treated"),
        "livestock":   sm("livestock"),
        "displaced":   sm("displaced"),
    }

    print(f"\n📊 Totals across all {len(rows)} submissions:")
    for k, v in kpis.items():
        if k != "submissions":
            print(f"   {k:15} {v}")

    # By Upazila
    uz_map = {}
    for r in rows:
        u = r["upazila"]
        if u not in uz_map:
            uz_map[u] = {"name":u,"submissions":0,"homes":0,"agri":0,
                         "schools":0,"deaths":0,"treated":0,"livestock":0,
                         "displaced":0,"flood_villages":0,"rain_villages":0}
        uz_map[u]["submissions"] += 1
        for k in ["homes","agri","schools","deaths","treated","livestock",
                  "displaced","flood_villages","rain_villages"]:
            uz_map[u][k] += r.get(k, 0)

    # By Disaster — check if des_raw contains each code/word
    def has(r, *codes):
        raw = r["des_raw"]
        return any(c in raw for c in codes)

    def dc(*codes):  return sum(1 for r in rows if has(r, *codes))
    def dsum(key, *codes): return sum(r[key] for r in rows if has(r, *codes))

    dis_data = [
        {"name":"Rainfall","bn":"অতিবৃষ্টি","color":"#4A90D9",
         "submissions":dc("des_1","rain"),
         "displaced":  dsum("rain_displaced","des_1","rain"),
         "agri":       round(dsum("rain_agri","des_1","rain"),1),
         "schools":    0,
         "treated":    0,
         "livestock":  0,
         "homes":      dsum("rain_homes","des_1","rain")},

        {"name":"Heatwave","bn":"তাপদাহ","color":"#E8743B",
         "submissions":dc("des_2","heat"),
         "displaced":  dsum("heat_displaced","des_2","heat"),
         "agri":       round(dsum("heat_agri","des_2","heat"),1),
         "schools":    dsum("heat_schools","des_2","heat"),
         "treated":    dsum("heat_treated","des_2","heat"),
         "livestock":  dsum("heat_livestock","des_2","heat"),
         "homes":      0},

        {"name":"Cold Wave","bn":"শৈত্যপ্রবাহ","color":"#5B8FF9",
         "submissions":dc("des_3","cold"),
         "displaced":  0,
         "agri":       round(dsum("cold_agri","des_3","cold"),1),
         "schools":    dsum("cold_schools","des_3","cold"),
         "treated":    dsum("cold_treated","des_3","cold"),
         "livestock":  dsum("cold_livestock","des_3","cold"),
         "homes":      0},

        {"name":"Drought","bn":"খরা","color":"#E84040",
         "submissions":dc("des_4","drought"),
         "displaced":  dsum("drought_displaced","des_4","drought"),
         "agri":       round(dsum("drought_agri","des_4","drought"),1),
         "schools":    dsum("drought_schools","des_4","drought"),
         "treated":    dsum("drought_treated","des_4","drought"),
         "livestock":  dsum("drought_livestock","des_4","drought"),
         "homes":      0},

        {"name":"Flood","bn":"বন্যা","color":"#2ECC71",
         "submissions":dc("des_5","flood"),
         "displaced":  dsum("flood_displaced","des_5","flood"),
         "agri":       round(dsum("flood_agri","des_5","flood"),1),
         "schools":    dsum("flood_schools","des_5","flood"),
         "treated":    dsum("flood_treated","des_5","flood"),
         "livestock":  0,
         "homes":      dsum("flood_homes","des_5","flood")},
    ]

    raw_out = [{
        "date":     r["date"],
        "upazila":  r["upazila"],
        "union":    r["union"],
        "disaster": r["disaster"][:40],
        "homes":    r["homes"],
        "agri":     round(r["agri"],1),
        "deaths":   r["deaths"],
        "treated":  r["treated"],
        "schools":  r["schools"],
        "displaced":r["displaced"],
        "needs":    r["needs"],
    } for r in rows]

    return {
        "kpis":      kpis,
        "upazila":   list(uz_map.values()),
        "disaster":  dis_data,
        "raw":       raw_out,
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

def update_html(data):
    if not os.path.exists(OUTPUT):
        print(f"❌ {OUTPUT} not found. Put both files in the same folder.")
        sys.exit(1)
    with open(OUTPUT, "r", encoding="utf-8") as f:
        html = f.read()
    new_data = f"const EMBEDDED = {json.dumps(data, ensure_ascii=False)};"
    html = re.sub(r"const EMBEDDED = \{.*?\};", new_data, html, flags=re.DOTALL)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n✅ {OUTPUT} updated with all 5 disaster types")

def main():
    results = fetch()
    data    = process(results)
    update_html(data)
    k = data["kpis"]
    print(f"\n🎉 Dashboard ready — {k['submissions']} submissions")
    print(f"\n👉 Drag '{OUTPUT}' to Netlify Deploys tab")
    print(f"   https://kurigramhazarddashboard.netlify.app\n")

if __name__ == "__main__":
    main()
