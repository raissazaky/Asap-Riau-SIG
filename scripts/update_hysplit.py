"""Perbarui semua data asap HYSPLIT di WebGIS dari file KMZ konsentrasi (READY).

Cara pakai (dari folder utama webgis, yang berisi index.html):
    1. Taruh SEMUA file .kmz konsentrasi ke folder  hysplit_kmz/   (nama file bebas)
    2. Jalankan:  python scripts/update_hysplit.py
Bulan dibaca otomatis dari isi KMZ (tanggal simulasi), bukan dari nama file.
KMZ trajektori (tanpa kontur konsentrasi) otomatis dilewati.

Yang diperbarui: data/hysplit/YYYY_MM.geojson, data/hysplit/paparan.json,
variabel asap_terpapar & asap_kelas di data/stats.json, dan data/ringkasan.json.
Hanya memakai pustaka bawaan Python 3.
"""
import glob, json, math, os, re, sys, zipfile
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KMZ_DIR = os.path.join(ROOT, "hysplit_kmz")
OUT = os.path.join(ROOT, "data", "hysplit")
NS = "{http://www.opengis.net/kml/2.2}"
KOTA = {"Pekanbaru": (101.45, 0.51), "Dumai": (101.45, 1.67), "Bengkalis": (102.11, 1.47), "Rengat": (102.55, -0.38),
        "Tembilahan": (103.15, -0.33), "Siak Sri Indrapura": (102.05, 0.80), "Bangkinang": (101.03, 0.33),
        "Bagansiapiapi": (100.81, 2.16), "Pasir Pengaraian": (100.30, 0.88), "Pangkalan Kerinci": (101.86, 0.40),
        "Singapura": (103.82, 1.35), "Batam": (104.03, 1.10), "Johor Bahru": (103.76, 1.49), "Melaka": (102.25, 2.19),
        "Kuala Lumpur": (101.69, 3.14), "Port Dickson": (101.80, 2.52), "Medan": (98.67, 3.59), "Padang": (100.35, -0.95),
        "Jambi": (103.61, -1.61), "Palembang": (104.76, -2.98), "Tanjungpinang": (104.45, 0.92)}


def kelas(exp):
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


def baca_kml(path):
    if path.lower().endswith(".kmz"):
        with zipfile.ZipFile(path) as z:
            nama = [n for n in z.namelist() if n.lower().endswith(".kml")]
            if not nama: return None
            return ET.fromstring(z.read(nama[0]))
    return ET.parse(path).getroot()


def olah(root):
    feats, src = [], []
    for pm in root.iter(NS + "Placemark"):
        name = (pm.findtext(NS + "name") or "").strip()
        if not name.startswith("Contour Level"): continue
        ts = pm.find(NS + "TimeSpan")
        exp = round(math.log10(float(re.search(r"([0-9.]+E[-+]?\d+)", name).group(1))))
        b = ts.findtext(NS + "begin")[:10]; e = ts.findtext(NS + "end")[:10]
        for poly in pm.iter(NS + "Polygon"):
            c = poly.find(f"{NS}outerBoundaryIs/{NS}LinearRing/{NS}coordinates").text.split()
            r = [[float(v.split(",")[0]), float(v.split(",")[1])] for v in c]
            if len(r) < 4: continue
            r = ring_simpl(r)
            if len(r) < 4 or area(r) < 0.0004: continue
            feats.append({"type": "Feature", "properties": {"level": exp, "kelas": kelas(exp), "mulai": b, "selesai": e},
                          "geometry": {"type": "Polygon", "coordinates": [r]}})
    for pm in root.iter(NS + "Placemark"):
        m = re.search(r"LAT:\s*([-.\d]+)\s+LON:\s*([-.\d]+)\s+Released between\s*([\d.]+)\.?\s*and\s*([\d.]+)",
                      pm.findtext(NS + "description") or "")
        if m: src.append([float(m.group(2)), float(m.group(1)), float(m.group(3)), float(m.group(4))])
    src = [list(t) for t in dict.fromkeys(tuple(round(v, 4) for v in s) for s in src)]  # buang duplikat
    for s in src:
        feats.append({"type": "Feature", "properties": {"sumber": True, "tinggi": "%g–%g m" % (s[2], s[3])},
                      "geometry": {"type": "Point", "coordinates": [s[0], s[1]]}})
    feats.sort(key=lambda f: (f["properties"].get("kelas", 9), f["properties"].get("mulai", "")))
    return feats, src


def main():
    files = sorted(glob.glob(os.path.join(KMZ_DIR, "*.km[lz]")) + glob.glob(os.path.join(KMZ_DIR, "*", "*.kml")))
    if not files: sys.exit(f"Tidak ada file .kmz/.kml di {KMZ_DIR}")
    os.makedirs(OUT, exist_ok=True)
    kab = json.load(open(os.path.join(ROOT, "data", "kabupaten.geojson"), encoding="utf-8"))
    STEP = 0.02; samples = {}
    for f in kab["features"]:
        g = f["geometry"]; ps = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        xs = [p[0] for q in ps for p in q[0]]; ys = [p[1] for q in ps for p in q[0]]; pts = []
        x = math.floor(min(xs) / STEP) * STEP
        while x <= max(xs):
            y = math.floor(min(ys) / STEP) * STEP
            while y <= max(ys):
                if any(inring(x, y, q[0]) for q in ps): pts.append((x, y))
                y += STEP
            x += STEP
        samples[f["properties"]["nama"]] = pts

    papf = os.path.join(OUT, "paparan.json")
    paparan = json.load(open(papf, encoding="utf-8")) if os.path.exists(papf) else {}
    for fp in files:
        root = baca_kml(fp)
        if root is None: continue
        feats, src = olah(root)
        polys = [(f["properties"]["kelas"], f["properties"]["mulai"], f["geometry"]["coordinates"][0]) for f in feats if "kelas" in f["properties"]]
        if not polys:
            print("lewati (bukan konsentrasi):", os.path.basename(fp)); continue
        days = sorted({p[1] for p in polys}); ym = days[0][:7].replace("-", "_")
        json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(OUT, ym + ".geojson"), "w"), separators=(",", ":"))

        def maxk(x, y, day=None):
            k = 0
            for kl, dd, r in polys:
                if (day is None or dd == day) and kl > k and inring(x, y, r): k = kl
            return k
        kabsum = {}
        for nm, pts in samples.items():
            ks = [maxk(x, y) for x, y in pts]; n = len(ks) or 1
            kabsum[nm] = {"terpapar_pct": round(100 * sum(1 for k in ks if k > 0) / n, 1),
                          "sedang_ke_atas_pct": round(100 * sum(1 for k in ks if k >= 3) / n, 1),
                          "kelas_maks": max(ks) if ks else 0,
                          "hari_terpapar": sum(1 for dd in days if any(maxk(x, y, dd) > 0 for x, y in pts[::7]))}
        kota = {k: maxk(*v) for k, v in KOTA.items()}
        paparan[ym] = {"hari": days, "n_poligon": len(polys), "sumber": src, "kab": kabsum,
                       "kota_kelas": {k: v for k, v in kota.items() if v > 0}}
        print(f"{ym}: {len(polys)} poligon, {len(src)} sumber, mulai {days[0]}  <- {os.path.basename(fp)}")
    paparan = dict(sorted(paparan.items()))
    json.dump(paparan, open(papf, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # stats.json
    sf = os.path.join(ROOT, "data", "stats.json"); S = json.load(open(sf, encoding="utf-8"))
    for k, d in S["data"].items():
        d["asap_terpapar"] = [paparan[m.replace("-", "_")]["kab"][k]["terpapar_pct"] if m.replace("-", "_") in paparan else None for m in S["months"]]
        d["asap_kelas"] = [paparan[m.replace("-", "_")]["kab"][k]["kelas_maks"] if m.replace("-", "_") in paparan else None for m in S["months"]]
    json.dump(S, open(sf, "w", encoding="utf-8"), ensure_ascii=False)

    # ringkasan.json
    rf = os.path.join(ROOT, "data", "ringkasan.json"); R = json.load(open(rf, encoding="utf-8"))
    R["paparan"] = {ym: {"hari": q["hari"], "kota": q["kota_kelas"], "n_sumber": len(q["sumber"])} for ym, q in paparan.items()}
    ser = []
    for i in range(len(S["months"])):
        xs = [S["data"][k]["asap_terpapar"][i] for k in S["data"] if S["data"][k]["asap_terpapar"][i] is not None]
        ser.append(round(sum(xs) / len(xs), 3) if xs else None)
    R["seri"]["asap_terpapar"] = ser
    for row in R["kab"]:
        xs = [x for x in S["data"][row["nama"]]["asap_terpapar"] if x is not None]
        row["asap"] = round(sum(xs) / len(xs), 1) if xs else None
    json.dump(R, open(rf, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"Selesai. Bulan dengan HYSPLIT: {', '.join(paparan)}")


if __name__ == "__main__":
    main()
