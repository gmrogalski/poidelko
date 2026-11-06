'use strict';
const el = id => document.getElementById(id);
let settings, latest = null, inflight = false, fetchError = false;

function badge(id, text, kind = '') {
  const node = el(id); node.textContent = text;
  node.className = (id === 'connection' ? 'badge ' : 'status ') + kind;
}
function clearNumbers() {
  for (const id of ['level', 'tds', 'voltage']) el(id).textContent = '—';
  el('bar').value = 0;
}
function empty(message, explanation) {
  latest = null; clearNumbers(); badge('connection', message, 'warn');
  badge('level-status', 'Oczekiwanie na pomiar');
  badge('tds-status', 'Oczekiwanie na pomiar');
  el('updated').textContent = explanation;
}
function validate(record) {
  const timestamp = Date.parse(record.created_at);
  if (!Number.isFinite(timestamp) || timestamp > Date.now() + 60000) throw Error('timestamp');
  const d = typeof record.value === 'string' ? JSON.parse(record.value) : record.value;
  if (!d || d.schema !== 1) throw Error('schema');
  for (const [key, max] of [['level_mm',100], ['tds_ppm',1000], ['tds_voltage',3.3]]) {
    if (d[key] !== null && (typeof d[key] !== 'number' || !Number.isFinite(d[key]) || d[key] < 0 || d[key] > max)) throw Error('value');
  }
  return { data: d, timestamp };
}
function render() {
  if (!latest) return;
  const { data: d, timestamp } = latest;
  const age = Math.max(0, Math.floor((Date.now() - timestamp) / 1000));
  const stale = age > settings.stale_after_s;
  badge('connection', fetchError ? 'Nie można odświeżyć danych' : stale ? 'Brak nowych pomiarów' : 'Dane aktualne', fetchError ? 'error' : stale ? 'warn' : 'ok');
  el('level').textContent = d.level_mm === null ? '—' : d.level_mm;
  el('bar').value = d.level_mm === null ? 0 : d.level_mm;
  el('tds').textContent = d.tds_ppm === null ? '—' : d.tds_ppm;
  el('voltage').textContent = d.tds_voltage === null ? '—' : d.tds_voltage.toFixed(3);
  if (stale || fetchError) {
    badge('level-status', 'Ostatnia znana wartość', 'warn');
    badge('tds-status', 'Ostatnia znana wartość', 'warn');
  } else {
    const threshold = Number.isFinite(d.low_level_mm) ? d.low_level_mm : 20;
    if (d.level_status === 'error') badge('level-status','Brak odpowiedzi czujnika','error');
    else if (d.level_status === 'inconsistent') badge('level-status','Sprawdź ułożenie czujnika','warn');
    else if (d.level_mm !== null && d.level_mm < threshold) badge('level-status','Niski poziom wody','warn');
    else badge('level-status',d.level_mm === null ? 'Brak odczytu' : 'Poziom powyżej progu alarmu',d.level_mm === null ? 'error' : 'ok');
    if (d.tds_status === 'out_of_range') badge('tds-status','Poza zakresem czujnika','warn');
    else if (d.tds_ppm === null) badge('tds-status','Brak odczytu','error');
    else badge('tds-status','Wynik orientacyjny','warn');
  }
  el('updated').textContent = 'Ostatni pomiar: ' + new Date(timestamp).toLocaleString('pl-PL') + ' · ' + age + ' s temu' + (stale ? ' · Sprawdź zasilanie i internet poidełka.' : ' · Odczyty przez Adafruit IO.');
}
async function refresh() {
  if (inflight || !settings) return;
  inflight = true;
  const controller = new AbortController(), timer = setTimeout(() => controller.abort(),10000);
  try {
    const endpoint = 'https://io.adafruit.com/api/v2/' + encodeURIComponent(settings.username) + '/feeds/' + encodeURIComponent(settings.feed) + '/data/last';
    const response = await fetch(endpoint, { cache: 'no-store', signal: controller.signal, credentials: 'omit' });
    if (response.status === 404) { empty('Oczekiwanie na dane','Kanał nie jest jeszcze publiczny albo nie otrzymał pierwszego pomiaru.'); return; }
    if (!response.ok) throw Error('HTTP');
    latest = validate(await response.json()); fetchError = false; render();
  } catch (error) {
    fetchError = true;
    if (latest) {
      render(); badge('connection','Nie można odświeżyć danych','error');
      badge('level-status','Ostatnia znana wartość','warn'); badge('tds-status','Ostatnia znana wartość','warn');
    } else empty('Brak połączenia z pomiarami','Nie udało się pobrać wyników. Spróbujemy ponownie automatycznie.');
  } finally { clearTimeout(timer); inflight = false; }
}
async function start() {
  try {
    const response = await fetch('./config.json',{cache:'no-store'});
    if (!response.ok) throw Error('config');
    settings = await response.json();
    if (!settings.username || !settings.feed) throw Error('config');
    settings.stale_after_s = Math.max(120, Number(settings.stale_after_s) || 180);
    await refresh();
    setInterval(refresh, Math.max(15000, Number(settings.poll_ms) || 15000));
    setInterval(render,1000);
  } catch (error) { empty('Konfiguracja w przygotowaniu','Strona czeka na konfigurację internetowego kanału pomiarowego.'); }
}
start();
