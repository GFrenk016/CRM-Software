/* ============================================================
   CRM — logica frontend (vanilla JS, nessuna dipendenza esterna).
   ============================================================ */

// --- SIDEBAR: collasso manuale + auto-collasso entrando in una sezione ------
function toggleSidebar() {
  const sb = document.getElementById('sidebar');
  sb.classList.toggle('collapsed');
  localStorage.setItem('sidebar-collapsed', sb.classList.contains('collapsed'));
}
(function initSidebar() {
  const sb = document.getElementById('sidebar');
  if (!sb) return;
  // Auto-collasso: nelle pagine di dettaglio/sezione si comprime per dare
  // spazio ai dati; la bacheca resta espansa. Preferenza salvata comunque.
  const saved = localStorage.getItem('sidebar-collapsed');
  const autoCollapse = document.body.dataset.section &&
                       document.body.dataset.section !== 'dashboard';
  if (saved === 'true' || (saved === null && autoCollapse)) {
    sb.classList.add('collapsed');
  }
})();

// --- MODALE generico --------------------------------------------------------
function openModal(html, large) {
  const ov = document.getElementById('modal-overlay');
  document.getElementById('modal-content').className = large ? 'modal modal-lg' : 'modal';
  document.getElementById('modal-body').innerHTML = html;
  ov.classList.remove('hidden');
}
function closeModal() {
  document.getElementById('modal-overlay').classList.add('hidden');
  document.getElementById('modal-body').innerHTML = '';
}
document.addEventListener('click', (e) => {
  if (e.target.id === 'modal-overlay') closeModal();
});
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeModal(); });

// Apre un frammento HTML già presente nella pagina (es. form nascosti)
function openTemplate(id, large) {
  const tpl = document.getElementById(id);
  if (tpl) openModal(tpl.innerHTML, large);
}

// --- TOAST ------------------------------------------------------------------
function toast(msg, type) {
  const tc = document.getElementById('toast-container');
  if (!tc) return;
  const t = document.createElement('div');
  t.className = 'toast ' + (type || 'success');
  t.textContent = msg;
  tc.appendChild(t);
  setTimeout(() => t.remove(), 3500);
}

// --- PIPELINE: drag & drop con persistenza sul DB ---------------------------
function initPipeline() {
  const cards = document.querySelectorAll('.kanban-card');
  const cols = document.querySelectorAll('.col-body');
  let dragged = null;

  cards.forEach(card => {
    card.draggable = true;
    card.addEventListener('dragstart', () => { dragged = card; card.classList.add('dragging'); });
    card.addEventListener('dragend', () => { card.classList.remove('dragging'); dragged = null; });
  });

  cols.forEach(col => {
    col.addEventListener('dragover', (e) => { e.preventDefault(); col.classList.add('drag-over'); });
    col.addEventListener('dragleave', () => col.classList.remove('drag-over'));
    col.addEventListener('drop', async (e) => {
      e.preventDefault();
      col.classList.remove('drag-over');
      if (!dragged) return;
      const stadio = col.dataset.stadio;
      const leadId = dragged.dataset.leadId;
      col.appendChild(dragged);
      updateColumnCounts();
      try {
        const r = await fetch('/pipeline/sposta', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ lead_id: parseInt(leadId), stadio })
        });
        const data = await r.json();
        if (data.ok) toast('Stadio aggiornato → ' + stadio);
        else toast('Errore aggiornamento', 'error');
      } catch (_) { toast('Errore di rete', 'error'); }
    });
  });
}
function updateColumnCounts() {
  document.querySelectorAll('.pipeline-col').forEach(col => {
    const n = col.querySelectorAll('.kanban-card').length;
    const badge = col.querySelector('.col-count');
    if (badge) badge.textContent = n;
  });
}

// --- INCASSI: click su cella di stato cicla da_incassare→incassato→in_ritardo
const CICLO_STATO = { da_incassare: 'incassato', incassato: 'in_ritardo', in_ritardo: 'da_incassare' };
const LABEL_STATO = { da_incassare: 'Da incassare', incassato: 'Incassato', in_ritardo: 'In ritardo' };
async function cicloIncasso(cell) {
  const id = cell.dataset.incassoId;
  const nuovo = CICLO_STATO[cell.dataset.stato] || 'da_incassare';
  try {
    const r = await fetch(`/incassi/${id}/stato`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ stato: nuovo })
    });
    const data = await r.json();
    if (!data.ok) return toast('Errore', 'error');
    cell.dataset.stato = data.stato;
    cell.className = 'mono-cell mc-' + data.stato;
    cell.textContent = LABEL_STATO[data.stato];
    const dc = document.querySelector(`.data-incasso[data-incasso-id="${id}"]`);
    if (dc) dc.textContent = data.data_incasso || '—';
    toast('Stato incasso: ' + LABEL_STATO[data.stato]);
  } catch (_) { toast('Errore di rete', 'error'); }
}

// --- ANTEPRIMA DOCUMENTI ----------------------------------------------------
function previewDoc(id, filename, isImg, isPdf) {
  let body = `<div class="modal-header"><h3>${filename}</h3>
    <button class="btn-icon" onclick="closeModal()">✕</button></div><div class="modal-body">`;
  const url = `/documenti/${id}/anteprima`;
  if (isImg) body += `<img src="${url}" class="preview-img" alt="${filename}">`;
  else if (isPdf) body += `<iframe src="${url}" class="preview-frame"></iframe>`;
  else body += `<p class="muted">Anteprima non disponibile per questo tipo di file.</p>`;
  body += `<div class="form-actions"><a class="btn btn-primary" href="/documenti/${id}/download">Scarica</a></div></div>`;
  openModal(body, true);
}

// --- MESSAGGISTICA WhatsApp / Email -----------------------------------------
function getSelectedClienti() {
  return Array.from(document.querySelectorAll('.sel-cliente:checked'))
    .map(cb => parseInt(cb.value));
}
function apriEditorMessaggio() {
  const ids = getSelectedClienti();
  if (!ids.length) return toast('Seleziona almeno un cliente', 'error');
  const html = `<div class="modal-header"><h3>Nuovo messaggio (${ids.length} destinatari)</h3>
    <button class="btn-icon" onclick="closeModal()">✕</button></div>
    <div class="modal-body">
      <div class="form-group"><label>Testo del messaggio</label>
        <textarea class="form-input" id="msg-text" rows="5" placeholder="Scrivi il messaggio..."></textarea></div>
      <div class="form-actions">
        <button class="btn btn-secondary" onclick="inviaMessaggi('email')">Invia via Email</button>
        <button class="btn btn-primary" onclick="inviaMessaggi('whatsapp')">Invia via WhatsApp</button>
      </div>
      <p class="muted" style="font-size:11px;margin-top:10px">Per invii multipli i messaggi si aprono uno alla volta, con conferma tra un destinatario e l'altro.</p>
    </div>`;
  openModal(html);
}
async function inviaMessaggi(canale) {
  const ids = getSelectedClienti();
  const testo = document.getElementById('msg-text').value.trim();
  if (!testo) return toast('Scrivi un messaggio', 'error');
  const r = await fetch('/messaggi/destinatari', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ids })
  });
  const { destinatari } = await r.json();
  closeModal();
  // Apertura sequenziale con conferma tra un destinatario e l'altro
  for (let i = 0; i < destinatari.length; i++) {
    const d = destinatari[i];
    let url = null;
    if (canale === 'whatsapp') {
      if (!d.wa) { alert(`${d.nome}: numero WhatsApp mancante, salto.`); continue; }
      url = `https://wa.me/${d.wa}?text=${encodeURIComponent(testo)}`;
    } else {
      if (!d.email) { alert(`${d.nome}: email mancante, salto.`); continue; }
      url = `mailto:${d.email}?subject=${encodeURIComponent('Messaggio')}&body=${encodeURIComponent(testo)}`;
    }
    if (i > 0 && !confirm(`Aprire il messaggio per ${d.nome}? (${i + 1}/${destinatari.length})`)) break;
    window.open(url, '_blank');
  }
}

// --- INIT -------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  if (document.querySelector('.pipeline-board')) initPipeline();
  // Ricerca rapida lato tabella (oltre al filtro SQL server-side)
  const quick = document.getElementById('quick-search');
  if (quick) {
    quick.addEventListener('input', (e) => {
      const v = e.target.value.toLowerCase();
      document.querySelectorAll('tbody tr[data-search]').forEach(row => {
        row.classList.toggle('hidden', !row.dataset.search.includes(v));
      });
    });
  }
  // Seleziona/deseleziona tutti
  const selAll = document.getElementById('sel-all');
  if (selAll) selAll.addEventListener('change', (e) => {
    document.querySelectorAll('.sel-cliente').forEach(cb => cb.checked = e.target.checked);
  });
});
