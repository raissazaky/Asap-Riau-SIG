// navbar + footer bersama untuk semua halaman
(function () {
  const here = (location.pathname.split("/").pop() || "index.html");
  const menu = [["index.html", "Beranda"], ["cara-kerja.html", "Cara Kerja"], ["metodologi.html", "Metodologi"],
                ["dashboard.html", "Dashboard"], ["tentang.html", "Tentang Kami"]];
  const nav = document.createElement("header");
  nav.className = "nav";
  nav.innerHTML = `<div class="wrap">
    <a class="brand" href="index.html"><span class="logo">AR</span><span><b>ASAP RIAU</b><small>WebGIS Bahaya & Dampak Asap Karhutla</small></span></a>
    <nav class="menu" id="menu">${menu.map(([h, t]) => `<a href="${h}" class="${h === here ? "aktif" : ""}">${t}</a>`).join("")}</nav>
    <div class="cta"><a class="btn btn-line" href="cara-kerja.html">Panduan</a><a class="btn btn-blue" href="dashboard.html">Buka Dashboard</a>
    <button class="burger" aria-label="Menu" onclick="document.getElementById('menu').classList.toggle('open')">☰</button></div></div>`;
  document.body.prepend(nav);
  if (document.body.dataset.nofooter) return;
  const f = document.createElement("footer");
  f.innerHTML = `<div class="wrap"><div class="cols">
    <div><div class="brand" style="margin-bottom:12px"><span class="logo">AR</span><span><b style="color:#fff">ASAP RIAU</b><small style="color:#93a3b8">PJBL SIG GD4103 · Kelompok 4 · K-05</small></span></div>
      <p style="max-width:420px">Sistem informasi geografis untuk memetakan kerawanan karhutla, sebaran asap (HYSPLIT) dan wilayah terdampak di Provinsi Riau, Januari–Oktober 2026.</p></div>
    <div><h5>NAVIGASI</h5>${menu.map(([h, t]) => `<a href="${h}">${t}</a>`).join("")}</div>
    <div><h5>SUMBER DATA</h5><a>NASA FIRMS MODIS C6.1 (titik panas & FRP)</a><a>NOAA ARL READY HYSPLIT</a><a>CHIRPS · ERA5-Land · MERRA-2</a><a>Sentinel-5P TROPOMI · MODIS MAIAC</a><a>CIFOR Peatland v2.1 · BIG (batas adm.)</a></div>
  </div><div class="copy"><span>© 2026 Kelompok 4 – Teknik Geodesi dan Geomatika ITB</span><span>Dibuat untuk tujuan akademik</span></div></div>`;
  document.body.append(f);
  const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add("on"); io.unobserve(e.target); } }), { threshold: .12 });
  document.querySelectorAll(".reveal").forEach(el => io.observe(el));
})();
// angka berjalan
function hitung(el, akhir, des = 0) {
  const t0 = performance.now(), d = 1100;
  (function f(t) { const p = Math.min(1, (t - t0) / d); el.textContent = (akhir * (1 - Math.pow(1 - p, 3))).toLocaleString("id-ID", { minimumFractionDigits: des, maximumFractionDigits: des }); if (p < 1) requestAnimationFrame(f); })(t0);
}
const BLN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"];
const namaBulan = ym => { const [y, m] = ym.split(/[-_]/); return BLN[+m - 1] + " " + y; };
