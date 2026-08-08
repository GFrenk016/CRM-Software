/* ============================================================
   CRM — logica frontend (vanilla JS, nessuna dipendenza esterna).
   ============================================================ */

// --- MODALE generico --------------------------------------------------------
function openModal(html, large) {
  const ov = document.getElementById('modal-overlay');
  document.getElementById('modal-content').className = large ? 'modal modal-lg' : 'modal';
  document.getElementById('modal-body').innerHTML = html;
  ov.classList.remove('hidden');
  // Il contenuto è appena entrato nel DOM: i suoi campi dinamici vanno
  // inizializzati ora, il DOMContentLoaded della pagina è passato da un pezzo.
  initContenutoModale();
}
function closeModal() {
  document.getElementById('modal-overlay').classList.add('hidden');
  document.getElementById('modal-body').innerHTML = '';
}
document.addEventListener('click', (e) => {
  if (e.target.id === 'modal-overlay') closeModal();
});
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeModal(); });

// Apre come pannello centrale un form servito dal server (?modal=1).
// Il form dentro il pannello è un <form> normale: al submit la pagina naviga e
// il server fa redirect + messaggio flash come sempre. Nessuna logica di
// salvataggio duplicata lato client.
async function apriFormModale(url, large) {
  const sep = url.includes('?') ? '&' : '?';
  try {
    const r = await fetch(`${url}${sep}modal=1`);
    if (!r.ok) throw new Error(r.status);
    openModal(await r.text(), large !== false);
  } catch (_) {
    // Se il pannello non si carica non lasciamo l'utente a mani vuote:
    // la pagina piena esiste ancora e fa esattamente le stesse cose.
    window.location.href = url;
  }
}

// Rimette in funzione, sul contenuto appena iniettato, gli init che altrimenti
// girerebbero solo al DOMContentLoaded della pagina. Gli handler delegati
// (ricerca cliente, ecc.) funzionano da soli e non hanno bisogno di nulla.
function initContenutoModale() {
  const scope = document.getElementById('modal-body');
  if (!scope) return;
  scope.querySelectorAll('select[name="tipologia"]').forEach(filtraStatiPratica);
  scope.querySelectorAll('[data-cliente-pratica]').forEach(caricaCollegabiliPratica);
  scope.querySelectorAll('[data-cliente-collegato]').forEach(caricaContrattiCliente);
  if (scope.querySelector('#cc-rows')) aggiornaConfrontoCompagnie();
}

// --- SINISTRO: contratti del solo cliente selezionato -----------------------
async function caricaContrattiCliente(selCliente) {
  const scope = selCliente.closest('form') || document;
  const campo = scope.querySelector('[data-contratti-cliente]');
  if (!campo) return;
  let contratti = [];
  if (selCliente.value) {
    try {
      const r = await fetch(`/contratti/del-cliente?cliente_id=${selCliente.value}`);
      contratti = (await r.json()).contratti || [];
    } catch (_) { return toast('Errore nel caricamento dei contratti', 'error'); }
  }
  const voluto = campo.dataset.selected || campo.value || '';
  campo.innerHTML = '';
  if (!contratti.length) {
    campo.innerHTML = '<option value="">— nessun contratto per questo cliente</option>';
  }
  contratti.forEach(k => {
    const o = document.createElement('option');
    o.value = k.id; o.textContent = k.label;
    if (String(k.id) === String(voluto)) o.selected = true;
    campo.appendChild(o);
  });
  campo.dataset.selected = '';
}

// Apre un frammento HTML già presente nella pagina (es. form nascosti)
function openTemplate(id, large) {
  const tpl = document.getElementById(id);
  if (tpl) openModal(tpl.innerHTML, large);   // openModal chiama già gli init
}

// --- PRATICA: contratto/sinistro/veicolo filtrati sul cliente scelto --------
// Prima i menu elencavano TUTTO il database, quindi era possibile collegare a
// una pratica il contratto di un altro cliente. Ora si ripopolano da
// /pratiche/collegabili a ogni cambio cliente. Il lead non è un menu: ogni
// cliente ne ha uno solo, quindi si mostra e basta (lo collega il server).
async function caricaCollegabiliPratica(selCliente) {
  const scope = selCliente.closest('form') || document;
  const campi = scope.querySelectorAll('[data-collegabile]');
  if (!campi.length) return;

  const clienteId = selCliente.value;
  let dati = { contratti: [], sinistri: [], veicoli: [], lead: null };
  if (clienteId) {
    try {
      const r = await fetch(`/pratiche/collegabili?cliente_id=${clienteId}`);
      dati = await r.json();
    } catch (_) {
      return toast('Errore nel caricamento dei collegamenti', 'error');
    }
  }

  campi.forEach(campo => {
    const tipo = campo.dataset.collegabile;

    if (tipo === 'lead') {
      // Sola lettura: niente <select>, niente valore inviato al server.
      campo.textContent = dati.lead ? dati.lead.label : 'Nessun lead';
      return;
    }

    // data-selected serve in modifica: al primo caricamento riseleziona il
    // valore già salvato, che a menu vuoto andrebbe perso.
    const voluto = campo.dataset.selected || campo.value || '';
    campo.innerHTML = '<option value="">—</option>';
    (dati[tipo] || []).forEach(v => {
      const o = document.createElement('option');
      o.value = v.id; o.textContent = v.label;
      if (String(v.id) === String(voluto)) o.selected = true;
      campo.appendChild(o);
    });
    // Consumato: dal secondo giro in poi vince la scelta dell'utente.
    campo.dataset.selected = '';
    if (!campo.options.length || campo.options.length === 1) {
      campo.options[0].textContent = '— nessuno per questo cliente';
    }
  });
}

// --- PRATICA: stati ammessi filtrati per tipologia --------------------------
// sinistro/consulenza/nuovo_preventivo non devono vedere gli stati di emissione.
// La mappa tipologia→stati arriva dal server in window.STATI_PER_TIPOLOGIA.
function filtraStatiPratica(tipoSel) {
  const map = window.STATI_PER_TIPOLOGIA || {};
  const scope = tipoSel.closest('form') || document;
  const statoSel = scope.querySelector('[data-stati-pratica]');
  if (!statoSel) return;
  const ammessi = map[tipoSel.value];
  const corrente = statoSel.value;
  Array.from(statoSel.options).forEach(o => {
    const ok = !ammessi || ammessi.includes(o.value);
    o.hidden = !ok; o.disabled = !ok;
  });
  // Se lo stato selezionato non è più ammesso, ripiega sul primo disponibile.
  if (ammessi && !ammessi.includes(corrente)) {
    const primo = Array.from(statoSel.options).find(o => !o.disabled);
    if (primo) statoSel.value = primo.value;
  }
}

// --- PREVENTIVO: righe ripetibili delle compagnie consultate ----------------
// Il subagente interpella più compagnie e ne confronta i premi: le righe si
// aggiungono/rimuovono in pagina e vengono inviate col form (niente fetch, gli
// indici vivi viaggiano nei campi ripetuti cc_idx). Nessuna libreria esterna:
// si clona il <template> già presente nella pagina, come per i modali.
let _ccProssimoIdx = null;

function aggiungiRigaCompagnia() {
  const tpl = document.getElementById('tpl-riga-compagnia');
  const cont = document.getElementById('cc-rows');
  if (!tpl || !cont) return;
  // Il primo indice libero si calcola dalle righe già in pagina: quelle salvate
  // sono numerate da 0, e riusare un indice sovrascriverebbe i campi di un'altra riga.
  if (_ccProssimoIdx === null) _ccProssimoIdx = cont.querySelectorAll('.cc-row').length;
  const idx = _ccProssimoIdx++;
  cont.insertAdjacentHTML('beforeend', tpl.innerHTML.replace(/__IDX__/g, idx));
  aggiornaConfrontoCompagnie();
}

function rimuoviRigaCompagnia(riga) {
  riga.remove();
  aggiornaConfrontoCompagnie();
}

// Evidenzia la riga col premio più basso. Un premio a zero/vuoto significa
// "compagnia interpellata ma non ancora quotata" e resta fuori dal confronto
// (stessa regola di Preventivo.premio_piu_basso lato server).
function aggiornaConfrontoCompagnie() {
  const righe = Array.from(document.querySelectorAll('#cc-rows .cc-row'));
  const vuoto = document.querySelector('.cc-empty');
  if (vuoto) vuoto.classList.toggle('hidden', righe.length > 0);
  let migliore = null, minimo = Infinity;
  righe.forEach(r => {
    const v = parseFloat(r.querySelector('.cc-premio').value);
    if (!isNaN(v) && v > 0 && v < minimo) { minimo = v; migliore = r; }
  });
  righe.forEach(r => {
    const ok = r === migliore;
    r.classList.toggle('is-migliore', ok);
    r.querySelector('.cc-migliore').classList.toggle('hidden', !ok);
  });
}

// Spuntare "Scelta" su una riga promuove quella compagnia: allinea subito i
// campi in alto (compagnia scelta + premio proposto) così si vede cosa si sta
// salvando. Lato server la riga spuntata vince comunque su quei campi.
function promuoviRigaCompagnia(riga) {
  const compagnia = riga.querySelector('.cc-compagnia').value;
  const premio = riga.querySelector('.cc-premio').value;
  const selScelta = document.getElementById('compagnia-scelta');
  const inpPremio = document.getElementById('premio-proposto');
  if (selScelta && compagnia) selScelta.value = compagnia;
  if (inpPremio && premio) inpPremio.value = premio;
}

document.addEventListener('click', (e) => {
  const rimuovi = e.target.closest('.cc-rimuovi');
  if (rimuovi) return rimuoviRigaCompagnia(rimuovi.closest('.cc-row'));
});
document.addEventListener('change', (e) => {
  const scelta = e.target.closest('.cc-scelta');
  if (scelta && scelta.checked) promuoviRigaCompagnia(scelta.closest('.cc-row'));
});
document.addEventListener('input', (e) => {
  const premio = e.target.closest('.cc-premio');
  if (!premio) return;
  aggiornaConfrontoCompagnie();
  // Se la riga è quella scelta, il premio proposto la segue senza risalvare.
  const riga = premio.closest('.cc-row');
  if (riga.querySelector('.cc-scelta').checked) promuoviRigaCompagnia(riga);
});

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

// --- ANTEPRIMA DEL FILE IN CARICAMENTO --------------------------------------
// Diversa da previewDoc(): lì il documento è già sul server e basta puntarne
// l'URL, qui il file esiste solo sul disco dell'utente, quindi va letto dal
// browser con FileReader. Serve a vedere cosa si sta per caricare prima di
// premere Carica, quando correggere costa solo un secondo clic.
function anteprimaUpload(input) {
  const box = document.getElementById('upload-preview');
  if (!box) return;
  const file = input.files && input.files[0];
  box.innerHTML = '';
  // Scelta annullata: via l'anteprima, altrimenti resterebbe quella del file
  // precedente e mostrerebbe qualcosa che non verrà caricato.
  if (!file) return box.classList.add('hidden');
  box.classList.remove('hidden');

  const media = document.createElement('div');
  media.className = 'upload-media';
  if (file.type.startsWith('image/')) {
    const img = document.createElement('img');
    img.className = 'upload-thumb';
    img.alt = file.name;
    // La lettura è asincrona: l'immagine è già nel DOM e si riempie dopo.
    const reader = new FileReader();
    reader.onload = (e) => { img.src = e.target.result; };
    reader.readAsDataURL(file);
    media.appendChild(img);
  } else {
    // PDF e affini: niente miniatura, solo l'icona del tipo file.
    media.innerHTML = '<svg class="icon icon-lg"><use href="#i-file-text"/></svg>';
  }

  const info = document.createElement('div');
  info.className = 'doc-info';
  const nome = document.createElement('div');
  nome.className = 'doc-nome';
  // textContent e non innerHTML: il nome del file arriva dall'utente e non
  // deve poter finire interpretato come markup.
  nome.textContent = file.name;
  nome.title = file.name;
  const meta = document.createElement('div');
  meta.className = 'doc-meta';
  meta.textContent = pesoLeggibile(file.size);
  info.append(nome, meta);
  box.append(media, info);
}

// I documenti già caricati mostrano i KB (lato server), qui si passa ai MB
// oltre il megabyte perché un allegato scelto a mano può essere molto grande
// e "8394 KB" si legge peggio di "8.2 MB".
function pesoLeggibile(bytes) {
  return bytes < 1024 * 1024 ? `${Math.round(bytes / 1024)} KB`
                             : `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
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

// --- ARCHIVIAZIONE massiva dei clienti spuntati -----------------------------
// Archiviare non cancella niente: il cliente esce da Anagrafica e Pipeline ma
// contratti, sinistri e incassi restano. Per questo basta una conferma leggera
// e non il confirm drammatico usato per le eliminazioni.
function archiviaSelezionati() {
  const ids = getSelectedClienti();
  if (!ids.length) return toast('Seleziona almeno un cliente da archiviare', 'error');
  const q = ids.length === 1 ? 'Archiviare il cliente selezionato?'
                             : `Archiviare i ${ids.length} clienti selezionati?`;
  if (!confirm(q + '\nI dati collegati restano, il cliente esce da elenco e Pipeline.')) return;

  const form = document.getElementById('form-archivia');
  form.innerHTML = '';
  ids.forEach(id => {
    const input = document.createElement('input');
    input.type = 'hidden'; input.name = 'ids'; input.value = id;
    form.appendChild(input);
  });
  form.submit();
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

// --- PRATICA: richiesta documenti al cliente --------------------------------
// Compone il link wa.me/mailto dai documenti mancanti (testo già pronto lato
// server) e lo apre, poi REGISTRA la comunicazione a sistema. Nessun invio
// automatico: il CRM prepara, l'operatore invia (stessa filosofia di messaggi).
async function richiediDocumenti(e) {
  e.preventDefault();
  const form = e.target;
  const testo = form.querySelector('.rich-doc-testo').value.trim();
  if (!testo) { toast('Nessun documento da richiedere', 'error'); return false; }
  const canale = form.querySelector('input[name="rich-doc-canale"]:checked').value;
  const wa = form.dataset.wa, email = form.dataset.email;
  let url, destinatario;
  if (canale === 'whatsapp') {
    if (!wa) { toast('Numero WhatsApp mancante per questo cliente', 'error'); return false; }
    destinatario = wa;
    url = `https://wa.me/${wa}?text=${encodeURIComponent(testo)}`;
  } else {
    if (!email) { toast('Email mancante per questo cliente', 'error'); return false; }
    destinatario = email;
    url = `mailto:${email}?subject=${encodeURIComponent('Documenti richiesti')}&body=${encodeURIComponent(testo)}`;
  }
  window.open(url, '_blank');
  try {
    await fetch(`/pratiche/${form.dataset.praticaId}/richiesta-documenti`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ canale, destinatario, testo })
    });
    toast('Richiesta preparata e registrata');
    setTimeout(() => location.reload(), 700);
  } catch (_) { toast('Link aperto, ma registrazione non riuscita', 'error'); }
  return false;
}

// --- INIT -------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  if (document.querySelector('.pipeline-board')) initPipeline();
  // Form pratica su pagina piena: i menu collegati nascono vuoti, vanno
  // riempiti col cliente già selezionato (in modifica riseleziona i valori
  // salvati grazie a data-selected).
  document.querySelectorAll('[data-cliente-pratica]').forEach(caricaCollegabiliPratica);
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
  // Form pratica a pagina piena: filtra gli stati per la tipologia già scelta.
  document.querySelectorAll('form select[name="tipologia"][data-filtra-stati]')
    .forEach(filtraStatiPratica);
  // Form preventivo: evidenzia subito il premio più basso fra quelli salvati.
  if (document.getElementById('cc-rows')) aggiornaConfrontoCompagnie();
});
