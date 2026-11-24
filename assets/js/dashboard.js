// ===================== ASAP RIAU – dashboard =====================
const B_GRID = [[-1.15, 100.0], [2.55, 103.85]], B_GAMBUT = [[-1.49991, 99.49986], [3.49969, 104.49947]];
const KELAS_ASAP = { 5: ["#a50026", "Sangat pekat (≥1E-10)"], 4: ["#f46d43", "Pekat (1E-11)"], 3: ["#fdae61", "Sedang (1E-12)"], 2: ["#9ecae1", "Tipis (1E-13)"], 1: ["#c6dbef", "Sangat tipis (≤1E-14)"] };
const PALET = { merah: ["#fee5d9", "#fcae91", "#fb6a4a", "#de2d26", "#a50f15"], biru: ["#eff3ff", "#bdd7e7", "#6baed6", "#3182bd", "#08519c"],
  ungu: ["#f2f0f7", "#cbc9e2", "#9e9ac8", "#756bb1", "#54278f"], hijau: ["#edf8e9", "#bae4b3", "#74c476", "#31a354", "#006d2c"], kerawanan: ["#1a9641", "#a6d96a", "#ffffbf", "#fdae61", "#d7191c"] };
const KOTA = { "Pekanbaru": [0.51, 101.45], "Dumai": [1.67, 101.45], "Bengkalis": [1.47, 102.11], "Rengat": [-0.38, 102.55], "Tembilahan": [-0.33, 103.15],
  "Siak Sri Indrapura": [0.80, 102.05], "Bangkinang": [0.33, 101.03], "Bagansiapiapi": [2.16, 100.81], "Pasir Pengaraian": [0.88, 100.30], "Pangkalan Kerinci": [0.40, 101.86],
  "Singapura": [1.35, 103.82], "Batam": [1.10, 104.03], "Johor Bahru": [1.49, 103.76], "Melaka": [2.19, 102.25], "Kuala Lumpur": [3.14, 101.69], "Port Dickson": [2.52, 101.80],
  "Medan": [3.59, 98.67], "Padang": [-0.95, 100.35], "Jambi": [-1.61, 103.61], "Palembang": [-2.98, 104.76], "Tanjungpinang": [0.92, 104.45] };
const RIAU = ["Pekanbaru", "Dumai", "Bengkalis", "Rengat", "Tembilahan", "Siak Sri Indrapura", "Bangkinang", "Bagansiapiapi", "Pasir Pengaraian", "Pangkalan Kerinci"];

const LAYERS = [
  { id: "ik", nama: "Kerawanan karhutla (AHP)", warna: "#d7191c", op: .7, on: true, tipe: "raster", pola: "IK" },
  { id: "asap", nama: "Sebaran asap HYSPLIT", warna: "#7c3aed", op: .6, on: true, tipe: "asap" },
  { id: "hot", nama: "Titik panas MODIS (FRP)", warna: "#f97316", op: .9, on: true, tipe: "hot" },
  { id: "kab", nama: "Choropleth kabupaten", warna: "#54278f", op: .0, on: true, tipe: "kab" },
  { id: "kota", nama: "Kota acuan", warna: "#0f172a", op: 1, on: true, tipe: "kota" },
  { id: "angin", nama: "Arah & kecepatan angin", warna: "#0369a1", op: .8, on: false, tipe: "angin" },
  { id: "fwi", nama: "Fire Weather Index", warna: "#e31a1c", op: .7, on: false, tipe: "raster", pola: "FWI" },
  { id: "ch", nama: "Curah hujan bulanan", warna: "#225ea8", op: .7, on: false, tipe: "raster", pola: "CH" },
  { id: "hth", nama: "Hari tanpa hujan berturut-turut", warna: "#fd8d3c", op: .7, on: false, tipe: "raster", pola: "HTH" },
  { id: "gambut", nama: "Lahan gambut (CIFOR)", warna: "#78481e", op: .55, on: false, tipe: "gambut" },
];
const LEG_RASTER = {
  IK: [["#1a9641", "Sangat rendah"], ["#a6d96a", "Rendah"], ["#ffffbf", "Sedang"], ["#fdae61", "Tinggi"], ["#d7191c", "Sangat tinggi"]],
  FWI: [["#ffffcc", "≤ 0,4"], ["#fed976", "0,4 – 1,2"], ["#fd8d3c", "1,2 – 2,2"], ["#e31a1c", "2,2 – 3,7"], ["#800026", "> 3,7"]],
  CH: [["#ffffd9", "≤ 126 mm"], ["#c7e9b4", "126 – 176"], ["#41b6c4", "176 – 214"], ["#225ea8", "214 – 259"], ["#081d58", "> 259 mm"]],
  HTH: [["#ffffcc", "≤ 3 hari"], ["#fed976", "3 – 4"], ["#fd8d3c", "4 – 6"], ["#e31a1c", "6 – 9"], ["#800026", "> 9 hari"]] };

let S, R, KAB, HOT, ANGIN, map, base, idx = 7, kabSel = "", hariSel = "all", timer = null;
const L_ = {}, cache = {}, opac = {}, aktif = {};
LAYERS.forEach(l => { opac[l.id] = l.op; aktif[l.id] = l.on; });
const ym = () => S.months[idx], ymU = () => ym().replace("-", "_");
const fmt = (x, d = 0) => x == null || isNaN(x) ? "–" : (+x).toLocaleString("id-ID", { minimumFractionDigits: d, maximumFractionDigits: d });
const getJSON = u => fetch(u).then(r => { if (!r.ok) throw u; return r.json(); });

Promise.all([getJSON("data/stats.json"), getJSON("data/ringkasan.json"), getJSON("data/kabupaten.geojson"), getJSON("data/hotspot.geojson"), getJSON("data/angin.geojson")])
  .then(([s, r, k, h, a]) => { S = s; R = r; KAB = k; HOT = h; ANGIN = a; init(); })
  .catch(e => { document.getElementById("map").innerHTML = `<p style="padding:20px">Gagal memuat data (${e}). Jalankan lewat server (Live Server / GitHub Pages), bukan dibuka langsung sebagai file.</p>`; });

function init() {
  map = L.map("map", { zoomControl: true, minZoom: 5 }).fitBounds(B_GRID);
  L.control.scale({ imperial: false, position: "bottomleft" }).addTo(map);
  ["grid", "kab", "asap", "traj", "titik"].forEach((n, i) => { map.createPane(n); map.getPane(n).style.zIndex = 380 + i * 20; });
  setBase("carto");
  // ui
  bulan.max = S.months.length - 1; bulan.value = idx;
  Object.keys(S.data).sort().forEach(k => kab.insertAdjacentHTML("beforeend", `<option>${k}</option>`));
  Object.entries(S.variabel).forEach(([k, v]) => varKab.insertAdjacentHTML("beforeend", `<option value="${k}">${v.nama}</option>`));
  varKab.value = "asap_terpapar";
  layers.innerHTML = LAYERS.map(l => `<div class="lyr ${l.on ? "" : "off"}" id="ly-${l.id}"><label><input type="checkbox" ${l.on ? "checked" : ""} data-id="${l.id}"><span class="dot" style="background:${l.warna}"></span>${l.nama}</label>
     ${l.tipe === "kota" ? "" : `<input type="range" min="0" max="1" step=".05" value="${l.id === "kab" ? .55 : l.op}" data-op="${l.id}" title="Transparansi">`}</div>`).join("");
  opac.kab = .55;
  layers.addEventListener("change", e => { const id = e.target.dataset.id; if (!id) return; aktif[id] = e.target.checked; document.getElementById("ly-" + id).classList.toggle("off", !aktif[id]); gambar(); });
  layers.addEventListener("input", e => { const id = e.target.dataset.op; if (!id) return; opac[id] = +e.target.value; setOpacity(id); });
  bulan.oninput = () => { idx = +bulan.value; perbarui(); };
  kab.onchange = () => { kabSel = kab.value; zoomKab(); perbarui(); };
  varKab.onchange = () => { gambar(); grafikRank(); };
  basemap.onchange = () => setBase(basemap.value);
  hari.onclick = e => { if (!e.target.dataset.h) return; hari.querySelectorAll("button").forEach(b => b.classList.toggle("on", b === e.target)); hariSel = e.target.dataset.h; gambar(); };
  play.onclick = () => { if (timer) { clearInterval(timer); timer = null; play.textContent = "▶"; return; } play.textContent = "⏸";
    timer = setInterval(() => { idx = (idx + 1) % S.months.length; bulan.value = idx; perbarui(); }, 1800); };
  legend = L.control({ position: "bottomright" }); legend.onAdd = () => (legendDiv = L.DomUtil.create("div", "legend")); legend.addTo(map);
  L.DomEvent.disableScrollPropagation(legendDiv);
  buatGrafik(); perbarui();
  if (!localStorageGet("tourDone")) setTimeout(() => tour(0), 700);
}
let legend, legendDiv;
function localStorageGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
function localStorageSet(k, v) { try { localStorage.setItem(k, v); } catch (e) { } }

function setBase(n) {
  if (base) map.removeLayer(base);
  const U = { carto: "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", dark: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    osm: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", esri: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}" };
  base = L.tileLayer(U[n], { maxZoom: 18, attribution: n === "esri" ? "Esri, Maxar" : n === "osm" ? "© OpenStreetMap" : "© OpenStreetMap © CARTO" }).addTo(map);
}
function zoomKab() {
  if (!kabSel) return map.fitBounds(B_GRID);
  const f = KAB.features.find(f => f.properties.nama === kabSel); if (f) map.fitBounds(L.geoJSON(f).getBounds(), { padding: [20, 20] });
}

async function perbarui() {
  const m = ym(); lblBulan.textContent = namaBulan(m); judulBulan.textContent = "· " + namaBulan(m);
  const p = R.paparan[ymU()];
  mapTag.textContent = p ? `${namaBulan(m)} · asap HYSPLIT mulai ${p.hari[0]} (72 jam)` : `${namaBulan(m)} · tidak ada simulasi HYSPLIT`;
  if (p && !cache[ymU()]) { try { cache[ymU()] = await getJSON(`data/hysplit/${ymU()}.geojson`); } catch (e) { cache[ymU()] = null; } }
  gambar(); ringkasan(); grafikTren(); grafikRank(); tabelPaparan();
}

function hapus(id) { if (L_[id]) { map.removeLayer(L_[id]); delete L_[id]; } }
function setOpacity(id) {
  const l = L_[id]; if (!l) return; const o = opac[id];
  if (l.setOpacity) return l.setOpacity(o);
  if (id === "asap") l.setStyle({ fillOpacity: o, opacity: Math.min(1, o + .2) });
  else if (id === "kab") l.setStyle(f => gayaKab(f));
  else if (id === "hot") l.setStyle({ fillOpacity: o, opacity: o });
  else if (id === "angin" || id === "traj") l.setStyle({ opacity: o });
}

function gambar() {
  const m = ym(), mu = ymU();
  LAYERS.forEach(l => hapus(l.id));
  LAYERS.forEach(l => {
    if (!aktif[l.id]) return;
    if (l.tipe === "raster") L_[l.id] = L.imageOverlay(`data/raster/${l.pola}_${mu}.png`, B_GRID, { opacity: opac[l.id], pane: "grid" }).addTo(map);
    if (l.tipe === "gambut") L_[l.id] = L.imageOverlay("data/raster/gambut.png", B_GAMBUT, { opacity: opac[l.id], pane: "grid" }).addTo(map);
    if (l.tipe === "kab") L_[l.id] = L.geoJSON(KAB, { pane: "kab", style: gayaKab, onEachFeature: (f, ly) => ly.bindPopup(() => popupKab(f.properties.nama)) }).addTo(map);
    if (l.tipe === "asap" && cache[mu]) {
      const hari = R.paparan[mu].hari, pilih = hariSel === "all" ? null : hari[+hariSel];
      L_[l.id] = L.geoJSON(cache[mu], { pane: "asap",
        filter: f => !f.properties.sumber && (!pilih || f.properties.mulai === pilih),
        style: f => ({ color: KELAS_ASAP[f.properties.kelas][0], weight: .4, fillColor: KELAS_ASAP[f.properties.kelas][0], fillOpacity: hariSel === "all" ? opac.asap * .55 : opac.asap, opacity: .6 }),
        onEachFeature: (f, ly) => { const p = f.properties; ly.bindPopup(`<b>Asap HYSPLIT</b><table><tr><td>Kelas</td><td>${p.kelas} – ${KELAS_ASAP[p.kelas][1]}</td></tr><tr><td>Konsentrasi relatif</td><td>1E${p.level} /m³</td></tr><tr><td>Periode</td><td>${p.mulai} s.d. ${p.selesai}</td></tr></table>`); } }).addTo(map);
      L.geoJSON(cache[mu], { pane: "titik", filter: f => f.properties.sumber, pointToLayer: (f, ll) => L.marker(ll, { icon: L.divIcon({ className: "", html: "<div style='font-size:20px;line-height:20px;text-shadow:0 0 3px #fff'>★</div>", iconSize: [20, 20], iconAnchor: [10, 10] }) })
        .bindPopup(`<b>Sumber emisi HYSPLIT</b><br>${ll.lat.toFixed(3)}, ${ll.lng.toFixed(3)}<br>Ketinggian pelepasan ${f.properties.tinggi}`) }).addTo(L_[l.id]);
    }
    if (l.tipe === "hot") {
      const fs = HOT.features.filter(f => f.properties.bulan === m && (!kabSel || f.properties.kab === kabSel));
      L_[l.id] = L.geoJSON({ type: "FeatureCollection", features: fs }, { pane: "titik",
        pointToLayer: (f, ll) => L.circleMarker(ll, { radius: 3 + Math.min(7, Math.sqrt(f.properties.frp || 1) / 2), color: "#7c2d12", weight: .8, fillColor: "#f97316", fillOpacity: opac.hot, opacity: opac.hot }),
        onEachFeature: (f, ly) => { const p = f.properties; ly.bindPopup(`<b>Titik panas MODIS</b><table><tr><td>Tanggal</td><td>${p.tanggal}</td></tr><tr><td>Kabupaten</td><td>${p.kab}</td></tr><tr><td>FRP</td><td>${fmt(p.frp, 1)} MW</td></tr><tr><td>Confidence</td><td>${p.confidence}%</td></tr></table>`); } }).addTo(map);
    }
    if (l.tipe === "angin") L_[l.id] = L.geoJSON({ type: "FeatureCollection", features: ANGIN.features.filter(f => f.properties.bulan === m) }, { pane: "traj",
      style: f => ({ color: "#0369a1", weight: .8 + f.properties.kec_ms * .9, opacity: opac.angin }), onEachFeature: (f, ly) => ly.bindTooltip(`${fmt(f.properties.kec_ms, 1)} m/s dari ${fmt(f.properties.arah_asal)}°`) }).addTo(map);
    if (l.tipe === "kota") {
      const kp = (R.paparan[mu] || { kota: {} }).kota;
      L_[l.id] = L.layerGroup(Object.entries(KOTA).filter(([n]) => RIAU.includes(n) || n in kp).map(([n, ll]) => {
        const k = kp[n] || 0;
        return L.circleMarker(ll, { pane: "titik", radius: 5, color: "#fff", weight: 2, fillColor: k ? KELAS_ASAP[k][0] : "#334155", fillOpacity: 1 })
          .bindTooltip(`${n}${k ? " · asap kelas " + k : ""}`, { direction: "top" }).bindPopup(`<b>${n}</b><br>${k ? "Dilalui asap kelas " + k + " (" + KELAS_ASAP[k][1] + ")" : "Tidak berada di kontur asap"} pada simulasi ${namaBulan(ym())}`);
      })).addTo(map);
    }
  });
  buatLegenda();
}

// ---------- choropleth ----------
function nilai(k, v, i = idx) { const a = (S.data[k] || {})[v]; return a ? a[i] : null; }
function breaks(v) {
  const xs = Object.keys(S.data).map(k => nilai(k, v)).filter(x => x != null && !isNaN(x)).sort((a, b) => a - b);
  if (!xs.length) return null; const q = p => xs[Math.min(xs.length - 1, Math.floor(p * xs.length))];
  return [q(.2), q(.4), q(.6), q(.8)];
}
function gayaKab(f) {
  const v = varKab.value, x = nilai(f.properties.nama, v), b = breaks(v), pal = PALET[S.variabel[v].palet] || PALET.merah;
  const c = x == null || !b ? null : pal[b.filter(t => x > t).length];
  const sel = kabSel === f.properties.nama;
  return { pane: "kab", color: sel ? "#f5b301" : "#1e293b", weight: sel ? 3 : 1, fillColor: c || "#e2e8f0", fillOpacity: c ? opac.kab : .1 };
}
function popupKab(n) {
  const rows = [["Titik panas", fmt(nilai(n, "hotspot"))], ["FRP total", fmt(nilai(n, "frp")) + " MW"], ["Luas kerawanan tinggi", fmt(nilai(n, "ik_tinggi"), 1) + " %"],
    ["Wilayah terpapar asap", fmt(nilai(n, "asap_terpapar"), 1) + " %"], ["Kelas asap maks.", fmt(nilai(n, "asap_kelas"))], ["PM2.5 MERRA-2", fmt(nilai(n, "pm25"), 1) + " µg/m³"],
    ["Curah hujan", fmt(nilai(n, "hujan")) + " mm"], ["Kelembapan", fmt(nilai(n, "rh"), 1) + " %"]];
  return `<b>${n}</b> · ${namaBulan(ym())}<table>${rows.map(r => `<tr><td>${r[0]}</td><td>${r[1]}</td></tr>`).join("")}</table>
    <a href="#" onclick="kab.value='${n}';kab.onchange();return false">Fokus ke kabupaten ini →</a>`;
}

function buatLegenda() {
  let h = "";
  LAYERS.filter(l => aktif[l.id]).forEach(l => {
    if (l.tipe === "raster") h += `<b>${l.nama}</b>` + LEG_RASTER[l.pola].map(([c, t]) => `<div><i style="background:${c}"></i>${t}</div>`).join("");
    if (l.tipe === "asap" && cache[ymU()]) h += `<b>Asap HYSPLIT (rata-rata 0–100 m)</b>` + [5, 4, 3, 2, 1].map(k => `<div><i style="background:${KELAS_ASAP[k][0]}"></i>${KELAS_ASAP[k][1]}</div>`).join("") + `<div>★ sumber emisi</div>`;
    if (l.tipe === "hot") h += `<b>Titik panas</b><div><i style="background:#f97316;border-radius:50%"></i>ukuran ∝ FRP (MW)</div>`;
    if (l.tipe === "gambut") h += `<b>Gambut</b><div><i style="background:#78481e"></i>Lahan gambut</div>`;
    if (l.tipe === "angin") h += `<b>Angin</b><div><span class="ln" style="background:#0369a1"></span>tebal = kencang</div>`;
    if (l.tipe === "kab") { const v = varKab.value, b = breaks(v), pal = PALET[S.variabel[v].palet] || PALET.merah;
      if (b) h += `<b>${S.variabel[v].nama} (${S.variabel[v].satuan})</b>` + pal.map((c, i) => `<div><i style="background:${c}"></i>${i ? "> " + fmt(b[i - 1], 1) : "≤ " + fmt(b[0], 1)}</div>`).join(""); }
  });
  legendDiv.innerHTML = h || "<i>Tidak ada layer aktif</i>";
}

// ---------- ringkasan ----------
function agg(v, i = idx) {
  if (kabSel) return nilai(kabSel, v, i);
  const xs = Object.keys(S.data).map(k => nilai(k, v, i)).filter(x => x != null);
  if (!xs.length) return null; const s = xs.reduce((a, b) => a + b, 0);
  return S.variabel[v].agregasi === "sum" ? s : s / xs.length;
}
function ringkasan() {
  ringkasNama.textContent = (kabSel || "Provinsi Riau") + " · " + namaBulan(ym());
  const k = [["Titik panas", fmt(agg("hotspot")), "or"], ["FRP total (MW)", fmt(agg("frp")), "or"], ["Luas kerawanan tinggi", fmt(agg("ik_tinggi"), 1) + "%", ""],
    ["Wilayah terpapar asap", fmt(agg("asap_terpapar"), 1) + "%", "pu"], ["PM2.5 MERRA-2 (µg/m³)", fmt(agg("pm25"), 1), "pu"], ["Curah hujan (mm)", fmt(agg("hujan")), ""]];
  kpis.innerHTML = k.map(([a, b, c]) => `<div class="kpi"><div class="v ${c}">${b}</div><div class="k">${a}</div></div>`).join("");
  const p = R.paparan[ymU()];
  if (!p) { kota.innerHTML = "<span>–</span>"; catHys.textContent = "Bulan ini tidak memiliki simulasi HYSPLIT."; return; }
  const e = Object.entries(p.kota).sort((a, b) => b[1] - a[1]);
  kota.innerHTML = e.length ? e.map(([n, c]) => `<span class="${RIAU.includes(n) ? "" : "lu"}" style="border-left:4px solid ${KELAS_ASAP[c][0]}">${n} · ${c}</span>`).join("") : "<span>Tidak ada</span>";
  const luar = e.filter(([n]) => !RIAU.includes(n)).map(([n]) => n);
  catHys.innerHTML = `Simulasi ${p.hari[0]} s.d. ${p.hari[p.hari.length - 1]} dari ${p.n_sumber} sumber. ` + (luar.length ? `<b>Asap melintas batas</b> ke ${luar.join(", ")}.` : "Asap tidak keluar jauh dari Riau.");
}

// ---------- grafik ----------
let cT, cR;
function buatGrafik() {
  if (!window.Chart) return;
  Chart.defaults.font.family = "'Plus Jakarta Sans',system-ui,sans-serif";
  cT = new Chart(cTren, { data: { labels: S.months.map(namaBulan), datasets: [
    { type: "bar", label: "Titik panas", data: [], backgroundColor: [], borderRadius: 5, yAxisID: "y" },
    { type: "line", label: "Terpapar asap (%)", data: [], borderColor: "#7c3aed", backgroundColor: "#7c3aed", tension: .35, yAxisID: "y1" },
    { type: "line", label: "Kerawanan tinggi (%)", data: [], borderColor: "#d7191c", backgroundColor: "#d7191c", borderDash: [5, 4], tension: .35, yAxisID: "y1" }] },
    options: { maintainAspectRatio: false, interaction: { mode: "index", intersect: false }, onClick: (e, el) => { if (el.length) { idx = el[0].index; bulan.value = idx; perbarui(); } },
      scales: { y: { title: { display: true, text: "titik panas" } }, y1: { position: "right", min: 0, max: 100, grid: { display: false }, title: { display: true, text: "%" } }, x: { grid: { display: false } } } } });
  cR = new Chart(cRank, { type: "bar", data: { labels: [], datasets: [{ data: [], backgroundColor: [], borderRadius: 5 }] },
    options: { indexAxis: "y", maintainAspectRatio: false, plugins: { legend: { display: false } }, onClick: (e, el) => { if (el.length) { kab.value = cR.data.labels[el[0].index]; kab.onchange(); } } } });
}
function grafikTren() {
  if (!cT) return; trenNama.textContent = kabSel || "Provinsi Riau";
  const ix = S.months.map((_, i) => i);
  cT.data.datasets[0].data = ix.map(i => agg("hotspot", i));
  cT.data.datasets[0].backgroundColor = ix.map(i => i === idx ? "#c2410c" : "#fdba74");
  cT.data.datasets[1].data = ix.map(i => agg("asap_terpapar", i));
  cT.data.datasets[2].data = ix.map(i => agg("ik_tinggi", i));
  cT.update();
}
function grafikRank() {
  if (!cR) return; const v = varKab.value, pal = PALET[S.variabel[v].palet] || PALET.merah;
  rankNama.textContent = `${S.variabel[v].nama} · ${namaBulan(ym())}`;
  const a = Object.keys(S.data).map(k => [k, nilai(k, v)]).filter(x => x[1] != null).sort((p, q) => q[1] - p[1]);
  cR.data.labels = a.map(x => x[0]); cR.data.datasets[0].data = a.map(x => x[1]);
  cR.data.datasets[0].backgroundColor = a.map(x => x[0] === kabSel ? "#f5b301" : pal[3]);
  cR.update();
}
function tabelPaparan() {
  papNama.textContent = namaBulan(ym());
  const p = R.paparan[ymU()];
  if (!p) { tPap.innerHTML = "<tr><td>Tidak ada simulasi HYSPLIT pada bulan ini.</td></tr>"; return; }
  const rows = Object.keys(S.data).map(k => [k, nilai(k, "asap_terpapar"), nilai(k, "asap_kelas"), nilai(k, "hotspot")]).sort((a, b) => (b[2] - a[2]) || (b[1] - a[1]));
  tPap.innerHTML = `<tr><th>Kabupaten/Kota</th><th>% wilayah terpapar</th><th>Kelas asap maksimum</th><th>Titik panas bulan ini</th></tr>` +
    rows.map(r => `<tr${r[0] === kabSel ? " style='background:#fff7e0'" : ""}><td>${r[0]}</td><td class="num"><div style="display:flex;gap:8px;align-items:center;justify-content:flex-end">${fmt(r[1], 1)}%<span style="display:inline-block;height:8px;width:${(r[1] || 0)}px;background:#7c3aed;border-radius:4px"></span></div></td>
      <td>${r[2] ? `<span class="badge" style="background:${KELAS_ASAP[r[2]][0]};color:${r[2] > 3 ? "#fff" : "#111"}">${r[2]}</span> ${KELAS_ASAP[r[2]][1]}` : "–"}</td><td class="num">${fmt(r[3])}</td></tr>`).join("");
}

// ---------- tur panduan ----------
const TUR = [["filter", "Filter & Layer", "Atur bulan, pilih kabupaten, nyalakan/matikan layer dan geser transparansinya di sini."],
  ["waktu", "Slider waktu", "Geser untuk berpindah bulan Januari–Oktober 2026, atau tekan ▶ untuk animasi."],
  ["ringkas", "Ringkasan Cepat", "Angka kunci bulan terpilih: titik panas, FRP, kerawanan, paparan asap, dan kota yang dilalui asap."],
  ["grafik", "Grafik Analisis", "Tren bulanan dan peringkat kabupaten. Klik batang grafik untuk berpindah bulan atau memilih kabupaten."]];
function tour(i) {
  document.querySelectorAll(".sorot").forEach(e => e.classList.remove("sorot"));
  if (i < 0 || i >= TUR.length) { document.getElementById("tour").classList.add("hide"); localStorageSet("tourDone", 1); return; }
  const [sel, j, isi] = TUR[i], el = document.querySelector(`[data-tour=${sel}]`);
  document.getElementById("tour").classList.remove("hide"); el.classList.add("sorot"); el.scrollIntoView({ block: "center", behavior: "smooth" });
  tStep.textContent = `LANGKAH ${i + 1} DARI ${TUR.length}`; tJudul.textContent = j; tIsi.textContent = isi;
  tNext.textContent = i === TUR.length - 1 ? "Selesai" : "Lanjut →";
  setTimeout(() => { const r = el.getBoundingClientRect(), bx = document.querySelector(".tbox");
    let x = r.right + 14, y = r.top; if (x + 330 > innerWidth) x = Math.max(10, r.left - 334); if (x < 10) { x = 10; y = r.bottom + 10; }
    bx.style.left = x + "px"; bx.style.top = Math.max(10, Math.min(innerHeight - 200, y)) + "px"; }, 350);
  tNext.onclick = () => tour(i + 1); tPrev.onclick = () => tour(Math.max(0, i - 1)); tSkip.onclick = () => tour(-1);
}
btnTour.onclick = () => tour(0);
