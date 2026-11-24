"""Menyiapkan data WebGIS dari hasil GEE / FIRMS.

Jalankan dari folder webgis (bisa lewat OSGeo4W Shell bawaan QGIS agar GDAL tersedia):

  1) Rekap tabel GEE  ->  data/stats.json
     python scripts/prepare_data.py stats --csv rekap_bulanan_kab.csv

  2) Hotspot FIRMS    ->  data/hotspot.geojson + kolom hotspot & frp di stats.json
     python scripts/prepare_data.py hotspot --firms fire_archive_SV-C2.csv fire_nrt_J1V-C2.csv

  4) HYSPLIT tdump   ->  data/hysplit/<nama>.geojson (segmen trajektori, field "jam")
     python scripts/prepare_data.py hysplit --tdump tdump_20260305 --nama 2026-03-05

  3) GeoTIFF bulanan  ->  PNG berwarna untuk Leaflet (butuh GDAL + numpy)
     python scripts/prepare_data.py raster --input folder_tif --prefix IK --mode kelas
     python scripts/prepare_data.py raster --input folder_tif --prefix AOD --mode kontinu

Syarat: data/kabupaten.geojson (EPSG:4326) dengan properti "nama".
"""
import argparse
import csv
import glob
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA = os.path.join(ROOT, "data")

META = {
    "ik_tinggi": ("Luas kelas tinggi–sangat tinggi", "% wilayah", "merah", "mean"),
    "hotspot": ("Jumlah hotspot", "titik", "merah", "sum"),
    "frp": ("Total FRP", "MW", "merah", "sum"),
    "burn_ha": ("Area terbakar (MCD64A1)", "ha", "merah", "sum"),
    "hujan": ("Curah hujan", "mm/bulan", "biru", "mean"),
    "hari_kering": ("Hari kering", "hari", "merah", "mean"),
    "suhu": ("Suhu udara", "°C", "merah", "mean"),
    "rh": ("Kelembapan relatif", "%", "biru", "mean"),
    "angin": ("Kecepatan angin", "m/s", "hijau", "mean"),
    "aod": ("AOD 550 nm", "", "ungu", "mean"),
    "co": ("CO total kolom", "mol/m²", "ungu", "mean"),
    "ai": ("Aerosol Index (UVAI)", "", "ungu", "mean"),
}
ORDER = list(META.keys())


# ---------------------------------------------------------------- utilitas
def norm(nama):
    s = (nama or "").lower()
    for _ in range(2):
        s = re.sub(r"^(kabupaten|kab\.?|kota adm\.?|kota)\s+", "", s.strip())
    return re.sub(r"[^a-z]", "", s)


def load_kab():
    path = os.path.join(DATA, "kabupaten.geojson")
    with open(path, encoding="utf-8") as f:
        gj = json.load(f)
    return gj


def month_range(a, b):
    y, m = map(int, a.split("-"))
    y1, m1 = map(int, b.split("-"))
    out = []
    while (y, m) <= (y1, m1):
        out.append("{}-{:02d}".format(y, m))
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def to_num(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    if v <= -9990 or v != v:
        return None
    return round(v, 4)


def write_stats(stats):
    with open(os.path.join(DATA, "stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False)


def read_stats():
    with open(os.path.join(DATA, "stats.json"), encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------- 1. stats
def cmd_stats(a):
    kab = load_kab()
    nama_gj = {norm(f["properties"]["nama"]): f["properties"]["nama"] for f in kab["features"]}
    rows = list(csv.DictReader(open(a.csv, encoding="utf-8-sig")))
    if not rows:
        sys.exit("CSV kosong.")
    cols = rows[0].keys()
    vars_ = [v for v in ORDER if v in cols]
    months = sorted({r["bulan"] for r in rows})
    months = month_range(months[0], months[-1])
    idx = {m: i for i, m in enumerate(months)}
    data, tak_cocok = {}, set()
    for r in rows:
        key = nama_gj.get(norm(r["nama"]))
        if key is None:
            tak_cocok.add(r["nama"])
            continue
        d = data.setdefault(key, {v: [None] * len(months) for v in vars_})
        for v in vars_:
            d[v][idx[r["bulan"]]] = to_num(r[v])
    stats = {"months": months,
             "variabel": {v: dict(zip(("nama", "satuan", "palet", "agregasi"), META[v])) for v in vars_},
             "data": data}
    if os.path.exists(os.path.join(DATA, "stats.json")) and a.keep_hotspot:
        old = read_stats()
        for v in ("hotspot", "frp"):
            if v in old["variabel"]:
                stats["variabel"][v] = old["variabel"][v]
                for k in data:
                    if k in old["data"] and v in old["data"][k] and old["months"] == months:
                        data[k][v] = old["data"][k][v]
    write_stats(stats)
    print("stats.json: {} kabupaten, {} bulan, variabel: {}".format(len(data), len(months), ", ".join(vars_)))
    if tak_cocok:
        print("PERINGATAN – nama tidak cocok dengan kabupaten.geojson:", ", ".join(sorted(tak_cocok)))


# ---------------------------------------------------------------- pembaca FIRMS
def baca_firms(path):
    """Membaca file FIRMS format CSV, JSON (list record / {"data": [...]}) atau GeoJSON.
    Menghasilkan dict dengan kunci latitude, longitude, acq_date, frp, confidence, type."""
    if path.lower().endswith((".json", ".geojson")):
        with open(path, encoding="utf-8-sig") as f:
            obj = json.load(f)
        if isinstance(obj, dict) and obj.get("type") == "FeatureCollection":
            recs = []
            for ft in obj["features"]:
                r = dict(ft.get("properties") or {})
                if ft.get("geometry") and ft["geometry"].get("type") == "Point":
                    r.setdefault("longitude", ft["geometry"]["coordinates"][0])
                    r.setdefault("latitude", ft["geometry"]["coordinates"][1])
                recs.append(r)
        elif isinstance(obj, dict):
            recs = next((v for v in obj.values() if isinstance(v, list)), [])
        else:
            recs = obj
    else:
        recs = csv.DictReader(open(path, encoding="utf-8-sig"))
    for r in recs:
        r = {str(k).lower(): v for k, v in r.items()}
        lat = r.get("latitude", r.get("lat"))
        lon = r.get("longitude", r.get("lon", r.get("lng")))
        tgl = str(r.get("acq_date", r.get("date", r.get("tanggal", ""))))
        if lat in (None, "") or lon in (None, "") or len(tgl) < 7:
            continue
        if tgl.isdigit() and len(tgl) >= 10:          # epoch milidetik
            tgl = dt_from_ms(int(tgl))
        r["latitude"], r["longitude"], r["acq_date"] = lat, lon, tgl[:10]
        r.setdefault("frp", r.get("frp_mw", 0))
        r.setdefault("confidence", "")
        r.setdefault("type", "")
        yield r


def dt_from_ms(ms):
    import datetime
    return datetime.datetime.utcfromtimestamp(ms / 1000).strftime("%Y-%m-%d")


# ---------------------------------------------------------------- 2. hotspot
def _rings(geom):
    if geom["type"] == "Polygon":
        return [geom["coordinates"]]
    if geom["type"] == "MultiPolygon":
        return geom["coordinates"]
    return []


def _in_ring(x, y, ring):
    inside, j = False, len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi:
            inside = not inside
        j = i
    return inside


def _in_poly(x, y, polys):
    for poly in polys:
        if _in_ring(x, y, poly[0]) and not any(_in_ring(x, y, h) for h in poly[1:]):
            return True
    return False


def cmd_hotspot(a):
    kab = load_kab()
    shapes = []
    for f in kab["features"]:
        polys = _rings(f["geometry"])
        xs = [p[0] for poly in polys for p in poly[0]]
        ys = [p[1] for poly in polys for p in poly[0]]
        shapes.append((f["properties"]["nama"], polys, (min(xs), min(ys), max(xs), max(ys))))
    keep_conf = set(a.conf.split(","))
    stats = read_stats()
    months = stats["months"]
    idx = {m: i for i, m in enumerate(months)}
    cnt = {s[0]: [0] * len(months) for s in shapes}
    frp = {s[0]: [0.0] * len(months) for s in shapes}
    feats, n_all, seen, n_dup = [], 0, set(), 0
    for path in a.firms:
        for r in baca_firms(path):
            n_all += 1
            kunci = (round(float(r["latitude"]), 4), round(float(r["longitude"]), 4),
                     r["acq_date"], str(r.get("acq_time", "")), str(r.get("satellite", "")))
            if kunci in seen:          # titik ganda archive vs NRT
                n_dup += 1
                continue
            seen.add(kunci)
            conf = str(r.get("confidence", "")).strip().lower()
            if conf.isdigit():
                if int(conf) < a.min_conf_modis:
                    continue
            elif conf and conf not in keep_conf:
                continue
            if str(r.get("type", "")) not in ("", "0", "None"):
                continue  # hanya kebakaran vegetasi (data standar)
            x, y = float(r["longitude"]), float(r["latitude"])
            tgl = r["acq_date"][:10]
            bulan = tgl[:7]
            if bulan not in idx:
                continue
            for nama, polys, (x0, y0, x1, y1) in shapes:
                if x0 <= x <= x1 and y0 <= y <= y1 and _in_poly(x, y, polys):
                    i = idx[bulan]
                    cnt[nama][i] += 1
                    frp[nama][i] += float(r.get("frp") or 0)
                    feats.append({"type": "Feature",
                                  "properties": {"bulan": bulan, "tanggal": tgl, "kab": nama,
                                                 "frp": to_num(r.get("frp")), "confidence": conf},
                                  "geometry": {"type": "Point", "coordinates": [round(x, 4), round(y, 4)]}})
                    break
    with open(os.path.join(DATA, "hotspot.geojson"), "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": feats}, f, separators=(",", ":"))
    for v in ("hotspot", "frp"):
        stats["variabel"][v] = dict(zip(("nama", "satuan", "palet", "agregasi"), META[v]))
    for nama in cnt:
        d = stats["data"].setdefault(nama, {})
        d["hotspot"] = cnt[nama]
        d["frp"] = [round(v, 1) for v in frp[nama]]
    # urutkan variabel sesuai ORDER
    # sisipkan hotspot & frp setelah variabel kerawanan, variabel lain tetap urut aslinya
    lama = [k for k in stats["variabel"] if k not in ("hotspot", "frp")]
    pos = max(0, min(len(lama), len([k for k in lama if k.startswith("ik_")])))
    urut = lama[:pos] + ["hotspot", "frp"] + lama[pos:]
    stats["variabel"] = {k: stats["variabel"][k] for k in urut}
    write_stats(stats)
    print("hotspot.geojson: {} dari {} baris FIRMS masuk wilayah & lolos filter ({} duplikat dibuang)".format(
        len(feats), n_all, n_dup))


# ---------------------------------------------------------------- 3. raster
KELAS = {1: (26, 150, 65), 2: (166, 217, 106), 3: (255, 255, 191), 4: (253, 174, 97), 5: (215, 25, 28)}
RAMP = [(255, 255, 204), (254, 217, 118), (253, 141, 60), (227, 26, 28), (128, 0, 38)]


def cmd_raster(a):
    try:
        from osgeo import gdal
        import numpy as np
    except ImportError:
        sys.exit("Butuh GDAL + numpy. Jalankan dari OSGeo4W Shell (QGIS) atau Python Console QGIS.")
    files = sorted(glob.glob(os.path.join(a.input, a.prefix + "_*.tif")))
    if not files:
        sys.exit("Tidak ada file {}_*.tif di {}".format(a.prefix, a.input))
    out_dir = os.path.join(DATA, "raster")
    os.makedirs(out_dir, exist_ok=True)

    lo = hi = None
    if a.mode == "kontinu":  # rentang warna sama untuk semua bulan
        vals = []
        for p in files:
            arr = gdal.Open(p).ReadAsArray().astype("float64")
            vals.append(arr[np.isfinite(arr) & (arr > -9990)])
        allv = np.concatenate(vals)
        lo, hi = np.percentile(allv, 2), np.percentile(allv, 98)
        print("Rentang warna {}: {:.4f} – {:.4f}".format(a.prefix, lo, hi))

    bounds = None
    for p in files:
        ds = gdal.Open(p)
        arr = ds.ReadAsArray().astype("float64")
        nd = ds.GetRasterBand(1).GetNoDataValue()
        rgba = np.zeros(arr.shape + (4,), dtype="uint8")
        valid = np.isfinite(arr) & (arr > -9990)
        if nd is not None:
            valid &= arr != nd
        if a.mode == "kelas":
            for k, (r, g, b) in KELAS.items():
                m = valid & (np.rint(arr) == k)
                rgba[m] = (r, g, b, 255)
        else:
            t = np.clip((arr - lo) / ((hi - lo) or 1), 0, 1) * (len(RAMP) - 1)
            i0 = np.floor(t).astype(int)
            i1 = np.minimum(i0 + 1, len(RAMP) - 1)
            f = (t - i0)[..., None]
            ramp = np.array(RAMP, dtype="float64")
            col = ramp[i0] * (1 - f) + ramp[i1] * f
            rgba[..., :3] = col.astype("uint8")
            rgba[..., 3] = np.where(valid, 255, 0)
            rgba[~valid] = 0
        mem = gdal.GetDriverByName("MEM").Create("", arr.shape[1], arr.shape[0], 4, gdal.GDT_Byte)
        for b in range(4):
            mem.GetRasterBand(b + 1).WriteArray(rgba[..., b])
        name = os.path.splitext(os.path.basename(p))[0] + ".png"
        gdal.GetDriverByName("PNG").CreateCopy(os.path.join(out_dir, name), mem)
        gt = ds.GetGeoTransform()
        bnd = [[gt[3] + gt[5] * ds.RasterYSize, gt[0]], [gt[3], gt[0] + gt[1] * ds.RasterXSize]]
        bounds = bounds or bnd
        print("  ", name)
    for aux in glob.glob(os.path.join(out_dir, "*.aux.xml")):
        os.remove(aux)
    b = [[round(v, 5) for v in pt] for pt in bounds]
    print("\nSalin bounds ini ke js/config.js untuk layer {}:\n  bounds: {}".format(a.prefix, json.dumps(b)))
    print("(Pastikan GeoTIFF berproyeksi EPSG:4326.)")


# ---------------------------------------------------------------- 4. hysplit
def cmd_hysplit(a):
    lines = open(a.tdump, encoding="utf-8", errors="ignore").read().splitlines()
    start = None
    for i, ln in enumerate(lines):
        if "PRESSURE" in ln.upper() or "THETA" in ln.upper():
            start = i + 1
            break
    if start is None:
        sys.exit("Format tdump tidak dikenali (baris nama variabel diagnostik tidak ditemukan).")
    traj = {}
    for ln in lines[start:]:
        p = ln.split()
        if len(p) < 12:
            continue
        try:
            tid, age = int(p[0]), float(p[8])
            lat, lon, h = float(p[9]), float(p[10]), float(p[11])
        except ValueError:
            continue
        traj.setdefault(tid, []).append((abs(age), lon, lat, h))
    feats = []
    for tid, pts in traj.items():
        pts.sort()
        for (a0, x0, y0, h0), (a1, x1, y1, h1) in zip(pts, pts[1:]):
            feats.append({"type": "Feature",
                          "properties": {"trajektori": tid, "jam": round(a1, 1), "tinggi_m": round(h1)},
                          "geometry": {"type": "LineString", "coordinates": [[x0, y0], [x1, y1]]}})
        a0, x0, y0, h0 = pts[0]
        feats.append({"type": "Feature", "properties": {"trajektori": tid, "jam": 0, "tinggi_m": round(h0),
                                                         "keterangan": "titik sumber"},
                      "geometry": {"type": "Point", "coordinates": [x0, y0]}})
    out = os.path.join(DATA, "hysplit", a.nama + ".geojson")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": feats}, f)
    print("{}: {} trajektori, {} segmen".format(out, len(traj), len(feats) - len(traj)))
    print('Daftarkan di js/config.js:\n  { nama: "Kejadian %s", file: "data/hysplit/%s.geojson", bulan: "%s" }'
          % (a.nama, a.nama, a.nama[:7]))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    s1 = sp.add_parser("stats")
    s1.add_argument("--csv", required=True)
    s1.add_argument("--keep-hotspot", action="store_true", help="pertahankan kolom hotspot/frp lama")
    s2 = sp.add_parser("hotspot")
    s2.add_argument("--firms", nargs="+", required=True)
    s2.add_argument("--conf", default="n,h", help="confidence VIIRS yang dipakai (default n,h)")
    s2.add_argument("--min-conf-modis", type=int, default=30)
    s3 = sp.add_parser("raster")
    s3.add_argument("--input", required=True)
    s3.add_argument("--prefix", required=True)
    s3.add_argument("--mode", choices=["kelas", "kontinu"], default="kelas")
    s4 = sp.add_parser("hysplit")
    s4.add_argument("--tdump", required=True)
    s4.add_argument("--nama", required=True, help="mis. 2026-03-05 (awali dengan YYYY-MM)")
    a = ap.parse_args()
    {"stats": cmd_stats, "hotspot": cmd_hotspot, "raster": cmd_raster, "hysplit": cmd_hysplit}[a.cmd](a)


if __name__ == "__main__":
    main()
