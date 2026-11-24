"""KMZ konsentrasi HYSPLIT (READY) -> GeoJSON per bulan + ringkasan paparan.
python3 -I kmz2geo.py <folder_x_*> <kabupaten.geojson> <out_dir>
"""
import glob, json, math, os, re, sys
import xml.etree.ElementTree as ET

SRC, KABF, OUT = sys.argv[1:4]
os.makedirs(OUT, exist_ok=True)
NS = "{http://www.opengis.net/kml/2.2}"
BULAN = {"JAN": "2026_01", "FEB": "2026_02", "Maret": "2026_03", "apr": "2026_04", "May": "2026_05",
         "JUL": "2026_07", "AUG": "2026_08", "Sep": "2026_09", "Okt": "2026_10"}

def kelas(exp):
    # eksponen konsentrasi relatif (unit release) -> 1..5
    return 5 if exp >= -10 else 4 if exp >= -11 else 3 if exp >= -12 else 2 if exp >= -13 else 1

def dp(pts, tol):
    if len(pts) < 5: return pts
    keep = [False] * len(pts); keep[0] = keep[-1] = True; st = [(0, len(pts) - 1)]
    while st:
        a, b = st.pop(); ax, ay = pts[a]; bx, by = pts[b]; dx, dy = bx - ax, by - ay; L = math.hypot(dx, dy) or 1e-12
        mx, mi = 0, -1
        for i in range(a + 1, b):
            d = abs(dy * pts[i][0] - dx * pts[i][1] + bx * ay - by * ax) / L
            if d > mx: mx, mi = d, i
        if mi > 0 and mx > tol: keep[mi] = True; st += [(a, mi), (mi, b)]
    return [p for p, k in zip(pts, keep) if k]

def ring_simpl(r, tol=0.004):
    o = r[:-1]
    if len(o) < 4: return r
    s = dp(o, tol); s.append(s[0])
    return [[round(x, 3), round(y, 3)] for x, y in s]

def area(r):
    return abs(sum(r[i][0] * r[i + 1][1] - r[i + 1][0] * r[i][1] for i in range(len(r) - 1))) / 2

def inring(x, y, r):
    ins = False; j = len(r) - 1
    for i in range(len(r)):
        xi, yi = r[i]; xj, yj = r[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi: ins = not ins
        j = i
    return ins

KOTA = {"Pekanbaru": (101.45, 0.51), "Dumai": (101.45, 1.67), "Bengkalis": (102.11, 1.47), "Rengat": (102.55, -0.38),
        "Tembilahan": (103.15, -0.33), "Siak Sri Indrapura": (102.05, 0.80), "Bangkinang": (101.03, 0.33),
        "Bagansiapiapi": (100.81, 2.16), "Pasir Pengaraian": (100.30, 0.88), "Pangkalan Kerinci": (101.86, 0.40),
        "Singapura": (103.82, 1.35), "Batam": (104.03, 1.10), "Johor Bahru": (103.76, 1.49), "Melaka": (102.25, 2.19),
        "Kuala Lumpur": (101.69, 3.14), "Port Dickson": (101.80, 2.52), "Medan": (98.67, 3.59), "Padang": (100.35, -0.95),
        "Jambi": (103.61, -1.61), "Palembang": (104.76, -2.98), "Tanjungpinang": (104.45, 0.92)}

# kabupaten
kab = json.load(open(KABF))
shapes = []
for f in kab["features"]:
    g = f["geometry"]; ps = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
    shapes.append((f["properties"]["nama"], ps))
# titik sampel grid 0,02 deg di tiap kab untuk luas terpapar
STEP = 0.02
samples = {}
for nm, ps in shapes:
    xs = [p[0] for q in ps for p in q[0]]; ys = [p[1] for q in ps for p in q[0]]
    pts = []
    x = math.floor(min(xs) / STEP) * STEP
    while x <= max(xs):
        y = math.floor(min(ys) / STEP) * STEP
        while y <= max(ys):
            if any(inring(x, y, q[0]) for q in ps): pts.append((x, y))
            y += STEP
        x += STEP
    samples[nm] = pts

summary = {}
for d in sorted(glob.glob(os.path.join(SRC, "x_*"))):
    key = os.path.basename(d)[2:].split("_")[0]
    if "traj" in os.path.basename(d): continue
    ym = BULAN[key]
    root = ET.parse(os.path.join(d, "HYSPLIT_html.kml")).getroot()
    feats, src = [], []
    for pm in root.iter(NS + "Placemark"):
        name = (pm.findtext(NS + "name") or "").strip()
        ts = pm.find(NS + "TimeSpan")
        if name.startswith("Contour Level"):
            exp = round(math.log10(float(re.search(r"([0-9.]+E[-+]?\d+)", name).group(1))))
            b = ts.findtext(NS + "begin")[:10]; e = ts.findtext(NS + "end")[:10]
            for poly in pm.iter(NS + "Polygon"):
                c = poly.find(f"{NS}outerBoundaryIs/{NS}LinearRing/{NS}coordinates").text.split()
                r = [[float(v.split(",")[0]), float(v.split(",")[1])] for v in c]
                if len(r) < 4: continue
                r = ring_simpl(r)
                if len(r) < 4 or area(r) < 0.0004: continue   # buang poligon < ~5 km2
                feats.append({"type": "Feature", "properties": {"level": exp, "kelas": kelas(exp), "mulai": b, "selesai": e},
                              "geometry": {"type": "Polygon", "coordinates": [r]}})
        elif "Soure" in name or (pm.find(NS + "Point") is not None and "Maximum" not in name and "LAT" in (pm.findtext(NS + "description") or "")):
            pass
    for pm in root.iter(NS + "Placemark"):
        desc = pm.findtext(NS + "description") or ""
        m = re.search(r"LAT:\s*([-.\d]+)\s+LON:\s*([-.\d]+)\s+Released between\s*([\d.]+)\.?\s*and\s*([\d.]+)", desc)
        if m:
            src.append([float(m.group(2)), float(m.group(1)), float(m.group(3)), float(m.group(4))])
    for s in src:
        feats.append({"type": "Feature", "properties": {"sumber": True, "tinggi": "%g–%g m" % (s[2], s[3])},
                      "geometry": {"type": "Point", "coordinates": [s[0], s[1]]}})
    # urut: kelas rendah dulu (digambar paling bawah)
    feats.sort(key=lambda f: (f["properties"].get("kelas", 9), f["properties"].get("mulai", "")))
    json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(OUT, ym + ".geojson"), "w"),
              separators=(",", ":"))
    polys = [(f["properties"]["kelas"], f["properties"]["mulai"], f["geometry"]["coordinates"][0]) for f in feats
             if "kelas" in f["properties"]]
    days = sorted({p[1] for p in polys})
    def maxk(x, y, day=None):
        k = 0
        for kl, dd, r in polys:
            if (day is None or dd == day) and kl > k and inring(x, y, r): k = kl
        return k
    kabsum = {}
    for nm, pts in samples.items():
        ks = [maxk(x, y) for x, y in pts]
        n = len(ks) or 1
        kabsum[nm] = {"terpapar_pct": round(100 * sum(1 for k in ks if k > 0) / n, 1),
                      "sedang_ke_atas_pct": round(100 * sum(1 for k in ks if k >= 3) / n, 1),
                      "kelas_maks": max(ks) if ks else 0,
                      "hari_terpapar": sum(1 for dd in days if any(maxk(x, y, dd) > 0 for x, y in pts[::7]))}
    kota = {k: maxk(*v) for k, v in KOTA.items()}
    allx = [p[0] for _, _, r in polys for p in r]; ally = [p[1] for _, _, r in polys for p in r]
    summary[ym] = {"hari": days, "n_poligon": len(polys), "sumber": src, "kab": kabsum,
                   "kota_kelas": {k: v for k, v in kota.items() if v > 0},
                   "bbox": [min(allx), min(ally), max(allx), max(ally)] if polys else None,
                   "level_ada": sorted({f["properties"]["level"] for f in feats if "level" in f["properties"]})}
    print(ym, len(polys), "poligon; hari", days, "; kota:", summary[ym]["kota_kelas"])
json.dump(summary, open(os.path.join(OUT, "_ringkasan_paparan.json"), "w"), ensure_ascii=False, indent=1)
