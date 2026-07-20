/* ============================================================
   CRM — logica frontend (vanilla JS, nessuna dipendenza esterna).
   ============================================================ */

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

// --- RICERCA CLIENTE INLINE (combobox) --------------------------------------
// Sostituisce il vecchio <select> lungo: si digita per filtrare, si clicca per
// selezionare. L'id scelto finisce nell'input hidden name="cliente_id" (il
// backend resta invariato). Delega su document cosi' funziona sia in pagina
// piena sia dentro il modale (il cui contenuto viene iniettato a runtime).
document.addEventListener('input', (e) => {
  const input = e.target.closest('.cliente-search-input');
  if (!input) return;
  const wrap = input.closest('[data-cliente-search]');
  const list = wrap.querySelector('.cliente-search-list');
  wrap.querySelector('input[type=hidden]').value = '';   // digitando si annulla la scelta
  const v = input.value.trim().toLowerCase();
  let visibili = 0;
  list.querySelectorAll('.cliente-search-item').forEach(it => {
    const match = it.dataset.name.includes(v);
    it.classList.toggle('hidden', !match);
    if (match) visibili++;
  });
  list.classList.toggle('hidden', visibili === 0);
});
document.addEventListener('click', (e) => {
  // Selezione di un cliente dalla lista
  const item = e.target.closest('.cliente-search-item');
  if (item) {
    const wrap = item.closest('[data-cliente-search]');
    wrap.querySelector('input[type=hidden]').value = item.dataset.id;
    wrap.querySelector('.cliente-search-input').value = item.textContent.trim();
    wrap.querySelector('.cliente-search-list').classList.add('hidden');
    return;
  }
  // Focus/click sul campo: mostra tutta la lista
  const input = e.target.closest('.cliente-search-input');
  if (input) {
    const list = input.closest('[data-cliente-search]').querySelector('.cliente-search-list');
    list.querySelectorAll('.cliente-search-item').forEach(it => it.classList.remove('hidden'));
    list.classList.remove('hidden');
    return;
  }
  // Click fuori: chiudi le liste aperte
  document.querySelectorAll('[data-cliente-search]').forEach(wrap => {
    if (!wrap.contains(e.target)) wrap.querySelector('.cliente-search-list').classList.add('hidden');
  });
});
// Impedisce l'invio senza un cliente valido (l'input hidden deve essere pieno)
document.addEventListener('submit', (e) => {
  const wrap = e.target.querySelector ? e.target.querySelector('[data-cliente-search]') : null;
  if (wrap && !wrap.querySelector('input[type=hidden]').value) {
    e.preventDefault();
    toast('Seleziona un cliente dalla lista', 'error');
    wrap.querySelector('.cliente-search-input').focus();
  }
});

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
