// js/app.js - table controls, client validation, API call, Gantt + results rendering
const COLORS = ['#a78bfa','#22d3ee','#fbbf24','#34d399','#f472b6','#60a5fa','#fb923c','#a3e635'];
const $ = id => document.getElementById(id);
let rows = [];  // model for the input table: [{pid, arrival, burst}]

// Escape text before putting it in innerHTML (prevents HTML injection from PIDs)
const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

// ---------- Input table ----------
function renderRows() {
  $('rows').innerHTML = rows.map((r, i) => `
    <tr>
      <td><input type="text" data-i="${i}" data-f="pid" value="${esc(r.pid)}" placeholder="P${i + 1}"></td>
      <td><input type="number" min="0" step="1" data-i="${i}" data-f="arrival" value="${esc(r.arrival)}"></td>
      <td><input type="number" min="1" step="1" data-i="${i}" data-f="burst" value="${esc(r.burst)}"></td>
      <td><button class="btn remove" type="button" data-remove="${i}" aria-label="Remove row">&times;</button></td>
    </tr>`).join('');
}
// Keep the model in sync while typing (event delegation: one listener for all inputs)
$('rows').addEventListener('input', e => {
  const { i, f } = e.target.dataset;
  if (f) rows[i][f] = e.target.value;
});
$('rows').addEventListener('click', e => {
  if (e.target.dataset.remove !== undefined) { rows.splice(+e.target.dataset.remove, 1); renderRows(); }
});
$('addBtn').onclick = () => { rows.push({ pid: 'P' + (rows.length + 1), arrival: 0, burst: 1 }); renderRows(); };
$('presetBtn').onclick = () => {   // edge-case preset from the spec (idle gaps + ties)
  rows = [{pid:'P1',arrival:5,burst:2},{pid:'P2',arrival:2,burst:3},{pid:'P3',arrival:12,burst:4},{pid:'P4',arrival:2,burst:1}];
  renderRows(); hideError();
};

// ---------- Algorithm selection ----------
const algo = () => document.querySelector('input[name=algo]:checked').value;
document.querySelectorAll('input[name=algo]').forEach(r =>
  r.onchange = () => { $('tqBox').hidden = algo() !== 'RR'; });   // show quantum only for RR

// ---------- Error banner ----------
function showError(msg) { $('error').textContent = msg; $('error').hidden = false; $('error').scrollIntoView({ block: 'nearest' }); }
function hideError() { $('error').hidden = true; }

// ---------- Client-side validation (server repeats it) ----------
function validate() {
  if (rows.length === 0) return 'Add at least one process.';
  const seen = new Set();
  for (let i = 0; i < rows.length; i++) {
    const r = rows[i], n = i + 1, pid = String(r.pid).trim();
    if (!pid) return `Row ${n}: PID cannot be empty.`;
    if (seen.has(pid)) return `Row ${n}: PID "${pid}" is duplicated.`;
    seen.add(pid);
    if (!/^-?\d+$/.test(String(r.arrival).trim())) return `Row ${n}: Arrival time must be a whole number.`;
    if (+r.arrival < 0) return `Row ${n}: Arrival time cannot be negative.`;
    if (!/^-?\d+$/.test(String(r.burst).trim())) return `Row ${n}: Burst time must be a whole number.`;
    if (+r.burst <= 0) return `Row ${n}: Burst time must be greater than 0.`;
  }
  if (algo() === 'RR' && (!/^\d+$/.test($('tq').value.trim()) || +$('tq').value <= 0))
    return 'Time quantum must be a whole number greater than 0.';
  return null;
}

// ---------- Run simulation: validate -> POST JSON -> render ----------
$('runBtn').onclick = async () => {
  hideError();
  const problem = validate();
  if (problem) return showError(problem);
  const payload = {
    algorithm: algo(),
    quantum: +$('tq').value,
    processes: rows.map(r => ({ pid: String(r.pid).trim(), arrival: +r.arrival, burst: +r.burst })),
  };
  try {
    const res = await fetch('api.php', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    const data = await res.json();
    if (!res.ok) return showError(data.error || 'Request failed.');   // HTTP 400 etc. -> banner
    render(data);
  } catch (err) { showError('Could not reach api.php. Is Apache running?'); }
};

// ---------- Rendering ----------
function render(d) {
  // Stable colour per PID (index in original input order)
  const color = {}; d.processes.forEach((p, i) => color[p.pid] = COLORS[i % COLORS.length]);

  // Gantt: flex-grow = duration makes every block width proportional to time
  $('gantt').innerHTML = d.gantt.map(b => {
    const idle = b.pid === 'IDLE', dur = b.end - b.start;
    return `<div class="seg" data-pid="${esc(b.pid)}" style="flex-grow:${dur}">
      <div class="block ${idle ? 'idle' : ''}" ${idle ? '' : `style="background:${color[b.pid]}"`}>${esc(b.pid)}</div>
      <div class="badge">${b.start} &ndash; ${b.end}</div></div>`;
  }).join('');

  // Results table (already in original input order from the backend)
  $('results').innerHTML = d.processes.map(p => `
    <tr data-pid="${esc(p.pid)}"><td><span class="dot" style="background:${color[p.pid]}"></span>${esc(p.pid)}</td>
    <td>${p.arrival}</td><td>${p.burst}</td><td>${p.completion}</td><td>${p.turnaround}</td><td>${p.waiting}</td></tr>`).join('');
  $('avgTat').textContent = d.avgTat.toFixed(2);
  $('avgWt').textContent = d.avgWt.toFixed(2);
  $('ganttCard').hidden = $('resultCard').hidden = false;
  sync();
}

// Sync Gantt <-> table: hovering a row or a block highlights every block of that PID
function sync() {
  const track = $('gantt');
  const focus = pid => {
    track.classList.toggle('focus', !!pid);
    track.querySelectorAll('.seg').forEach(s => s.classList.toggle('hl', s.dataset.pid === pid));
  };
  document.querySelectorAll('#results tr, #gantt .seg').forEach(el => {
    el.onmouseenter = () => focus(el.dataset.pid);
    el.onmouseleave = () => focus(null);
  });
}

// ---------- Initial state: a small sample so the page is not empty ----------
rows = [{pid:'P1',arrival:0,burst:5},{pid:'P2',arrival:1,burst:3},{pid:'P3',arrival:2,burst:8}];
renderRows();
