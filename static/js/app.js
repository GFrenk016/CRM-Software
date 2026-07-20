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

// --- INCASSI: dropdown di stato esplicito per riga (niente più ciclo a click) --
const LABEL_STATO = { da_incassare: 'Da incassare', incassato: 'Incassato', in_ritardo: 'In ritardo' };
async function cambiaStatoIncasso(sel) {
  const id = sel.dataset.incassoId;
  const nuovo = sel.value;
  try {
    const r = await fetch(`/incassi/${id}/stato`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ stato: nuovo })
    });
    const data = await r.json();
    if (!data.ok) return toast('Errore', 'error');
    // Aggiorna la colorazione della cella e la data incasso senza ricaricare.
    sel.className = 'mono-cell mc-' + data.stato;
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

// --- DOCUMENTI: filtro per tipo (client-side, i documenti sono già in pagina) --
function filtraDocumenti(tipo) {
  const items = document.querySelectorAll('#doc-list .related-item');
  let visibili = 0;
  items.forEach(it => {
    const match = !tipo || it.dataset.tipo === tipo;
    it.classList.toggle('hidden', !match);
    if (match) visibili++;
  });
  const empty = document.getElementById('doc-empty-filtro');
  if (empty) empty.classList.toggle('hidden', !(tipo && items.length && visibili === 0));
}

// --- MESSAGGISTICA WhatsApp / Email -----------------------------------------
// La modale è raggiungibile globalmente dalla sidebar (apriMessaggio senza
// argomenti) e dalla lista clienti passando gli id già spuntati (pre-selezione).
// NB: un invio massivo REALE e automatizzato richiederebbe un backend dedicato
// (WhatsApp Business API / email transazionale). Qui generiamo solo i link.
function getSelectedClienti() {
  return Array.from(document.querySelectorAll('.sel-cliente:checked'))
    .map(cb => parseInt(cb.value));
}

let _msgTemplates = [];

async function apriMessaggio(preIds) {
  preIds = preIds || [];
  let data;
  try {
    const r = await fetch('/messaggi/config');
    data = await r.json();
  } catch (_) { return toast('Errore nel caricamento clienti', 'error'); }
  _msgTemplates = data.templates || [];

  const opts = _msgTemplates.map((t, idx) =>
    `<option value="${idx}">${t.label}</option>`).join('');
  const lista = data.clienti.map(c => {
    const canali = [c.has_wa ? 'WhatsApp' : null, c.has_email ? 'Email' : null]
      .filter(Boolean).join(' · ') || 'nessun contatto';
    const checked = preIds.includes(c.id) ? 'checked' : '';
    return `<label class="msg-cliente-item" data-name="${c.nome.toLowerCase()}">
        <input type="checkbox" class="msg-sel" value="${c.id}" ${checked}>
        <span class="msg-cliente-nome">${c.nome}</span>
        <span class="muted" style="font-size:11px;margin-left:auto">${canali}</span>
      </label>`;
  }).join('');

  const html = `<div class="modal-header"><h3>Nuovo messaggio</h3>
      <button class="btn-icon" onclick="closeModal()"><svg class="icon"><use href="#i-x"/></svg></button></div>
    <div class="modal-body">
      <div class="form-group"><label>Destinatari (uno o più)</label>
        <input class="form-input" id="msg-filtro" placeholder="Filtra clienti..." style="margin-bottom:6px">
        <div class="msg-cliente-list" id="msg-cliente-list">${lista}</div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>Canale</label>
          <div class="radio-group">
            <label class="radio-row"><input type="radio" name="msg-canale" value="whatsapp" checked> WhatsApp</label>
            <label class="radio-row"><input type="radio" name="msg-canale" value="email"> Email</label>
          </div>
        </div>
        <div class="form-group"><label>Messaggio preimpostato</label>
          <select class="form-input" id="msg-template" onchange="applicaTemplate()">${opts}</select>
        </div>
      </div>
      <div class="form-group"><label>Testo · modificabile — {nome} = nome del cliente</label>
        <textarea class="form-input" id="msg-text" rows="5" placeholder="Scrivi il messaggio..."></textarea></div>
      <div class="form-actions">
        <button type="button" class="btn btn-secondary" onclick="closeModal()">Annulla</button>
        <button type="button" class="btn btn-primary" onclick="inviaMessaggi()">
          <svg class="icon icon-sm"><use href="#i-message"/></svg> Invia</button>
      </div>
      <p class="muted" style="font-size:11px;margin-top:8px">Per più destinatari i messaggi si aprono uno alla volta, con conferma tra l'uno e l'altro (evita il blocco pop-up del browser).</p>
    </div>`;
  openModal(html, true);
}

// Applica il testo del template scelto nel textarea (resta poi modificabile).
function applicaTemplate() {
  const sel = document.getElementById('msg-template');
  const t = _msgTemplates[parseInt(sel.value)];
  if (t) document.getElementById('msg-text').value = t.testo;
}

// Filtro live sulla lista destinatari nella modale.
document.addEventListener('input', (e) => {
  if (e.target.id !== 'msg-filtro') return;
  const v = e.target.value.trim().toLowerCase();
  document.querySelectorAll('#msg-cliente-list .msg-cliente-item').forEach(it => {
    it.classList.toggle('hidden', !it.dataset.name.includes(v));
  });
});

async function inviaMessaggi() {
  const ids = Array.from(document.querySelectorAll('.msg-sel:checked'))
    .map(cb => parseInt(cb.value));
  if (!ids.length) return toast('Seleziona almeno un destinatario', 'error');
  const testo = document.getElementById('msg-text').value.trim();
  if (!testo) return toast('Scrivi un messaggio', 'error');
  const canale = document.querySelector('input[name="msg-canale"]:checked').value;

  const r = await fetch('/messaggi/destinatari', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ids })
  });
  const { destinatari } = await r.json();
  closeModal();

  // Apertura sequenziale con conferma tra un destinatario e l'altro: evita che
  // il browser blocchi troppe schede aperte in una sola volta.
  // NB: un invio massivo reale e automatizzato richiederebbe un'integrazione
  // backend (WhatsApp Business API / email transazionale).
  let inviati = 0;
  for (let i = 0; i < destinatari.length; i++) {
    const d = destinatari[i];
    const msg = testo.replace(/\{nome\}/g, d.nome || '');
    let url = null;
    if (canale === 'whatsapp') {
      if (!d.wa) { toast(`${d.nome_completo}: numero WhatsApp mancante, salto.`, 'error'); continue; }
      url = `https://wa.me/${d.wa}?text=${encodeURIComponent(msg)}`;
    } else {
      if (!d.email) { toast(`${d.nome_completo}: email mancante, salto.`, 'error'); continue; }
      url = `mailto:${d.email}?subject=${encodeURIComponent('Comunicazione dalla sua assicurazione')}&body=${encodeURIComponent(msg)}`;
    }
    if (i > 0 && !confirm(`Aprire il messaggio per ${d.nome_completo}? (${i + 1}/${destinatari.length})`)) break;
    window.open(url, '_blank');
    inviati++;
  }
  if (inviati) toast(`${inviati} messaggio/i aperti in nuove schede`);
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
