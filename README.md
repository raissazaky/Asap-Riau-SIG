# ASAP RIAU – WebGIS Bahaya & Dampak Asap Karhutla Riau (Jan–Okt 2026)
PJBL SIG GD4103 · Kelompok 4 · Kelas 05 · Teknik Geodesi dan Geomatika ITB

## Halaman
- `index.html` Beranda · `cara-kerja.html` Cara Kerja · `metodologi.html` Metodologi
- `dashboard.html` Dashboard peta (slider waktu, filter kabupaten, layer + transparansi, HYSPLIT per hari, ringkasan, grafik, tur panduan)
- `tentang.html` Tentang Kami (ganti nama/NIM anggota di bagian `const TIM` paling bawah file)

## Menjalankan
Buka folder di VS Code → klik kanan `index.html` → Open with Live Server, atau unggah ke GitHub Pages.
Tidak bisa dibuka dengan klik dua kali (data dimuat lewat fetch).

## Data (folder `data/`)
- `stats.json` statistik bulanan per kabupaten (termasuk `asap_terpapar`, `asap_kelas`)
- `ringkasan.json` angka untuk grafik & kartu
- `hysplit/2026_MM.geojson` kontur konsentrasi HYSPLIT tim (KMZ → GeoJSON), `traj_2026_03.geojson`, `paparan.json`
- `raster/` PNG IK, FWI, CH, HTH bulanan + gambut · `hotspot.geojson` FIRMS MODIS · `angin.geojson`

## Memperbarui HYSPLIT 
1. Taruh file KMZ konsentrasi ke folder `hysplit_kmz/` (nama file bebas; bulan dibaca dari isi KMZ).
2. Dari folder ini jalankan: `python scripts/update_hysplit.py`
3. Refresh browser. Peta, ringkasan, grafik dan tabel paparan ikut terisi.
