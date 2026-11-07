let currentConfig = { root_dir: '', auto_open: true, close_on_convert: false };
let activeTab = 'text';
let selectedFilePath = '';
let lastGeneratedResult = null;

function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2200);
}

async function fetchWithRetry(url, options = {}, retries = 2, delayMs = 350, timeoutMs = 8000) {
  let lastErr;
  for (let i = 0; i < retries; i++) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const fetchOptions = { ...options, signal: controller.signal };
      const res = await fetch(url, fetchOptions);
      clearTimeout(timeoutId);
      return res;
    } catch (err) {
      clearTimeout(timeoutId);
      lastErr = err;
      console.warn(`[App] Intento ${i + 1}/${retries} para ${url} falló:`, err);
      if (i < retries - 1) {
        await new Promise(r => setTimeout(r, delayMs));
      }
    }
  }
  throw lastErr;
}

async function loadConfig() {
  try {
    const res = await fetchWithRetry('/api/config');
    const data = await res.json();
    currentConfig = data;
    document.getElementById('currentDirPath').textContent = data.root_dir;
    document.getElementById('currentDirPath').title = data.root_dir;
    document.getElementById('autoOpenToggle').checked = !!data.auto_open;
    const closeToggle = document.getElementById('closeOnConvertToggle');
    if (closeToggle) {
      closeToggle.checked = !!data.close_on_convert;
    }
    renderRecentList(data.recent_conversions || []);
  } catch (err) {
    console.error('Error cargando configuración:', err);
  }
}

function renderRecentList(list) {
  const el = document.getElementById('recentList');
  const countEl = document.getElementById('recentCount');
  if (countEl) {
    countEl.textContent = list && list.length > 0 ? `(${list.length})` : '';
  }
  if (!list || list.length === 0) {
    el.innerHTML = `
      <div class="recent-empty">
        <span class="recent-empty-icon">📂</span>
        <div style="font-weight: 550;">No hay documentos en el historial</div>
        <div style="font-size: 0.74rem; opacity: 0.7;">Cada documento HTML que conviertas se registrará aquí con acceso rápido.</div>
      </div>`;
    return;
  }
  el.innerHTML = list.map(item => `
    <div class="recent-item">
      <div class="recent-info">
        <span class="recent-item-title" title="${escapeHtml(item.title || item.filename)}">${escapeHtml(item.title || item.filename)}</span>
        <span class="recent-item-meta"><code>${escapeHtml(item.filename)}</code> · 📅 ${escapeHtml(item.timestamp || '')}</span>
      </div>
      <div class="recent-actions-group">
        <button class="btn-compact" onclick="openUrl('${escapeAttr(item.file_url)}')" title="Abrir en el navegador">🌐 Abrir</button>
        <button class="btn-compact" onclick="copyText('${escapeAttr(item.file_url)}', 'Enlace copiado al portapapeles')" title="Copiar enlace">📋 Copiar</button>
        <button class="btn-compact btn-delete" onclick="deleteRecentDoc('${escapeAttr(item.filename)}', '${escapeAttr(item.file_path)}', '${escapeAttr(item.title || item.filename)}')" title="Eliminar documento y borrar archivo HTML">🗑️ Eliminar</button>
      </div>
    </div>
  `).join('');
}

function escapeHtml(str) {
  return (str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function escapeAttr(str) {
  return (str || '').replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

async function deleteRecentDoc(filename, filePath, docTitle) {
  const displayName = docTitle || filename || 'este documento';
  const confirmed = window.confirm(`¿Estás seguro de que deseas eliminar este documento?\n\n"${displayName}"\n\nEsta acción borrará permanentemente el archivo HTML del disco y lo quitará del historial.`);
  if (!confirmed) return;

  try {
    const res = await fetch('/api/delete-document', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename: filename, file_path: filePath })
    });
    const data = await res.json();
    if (data.success) {
      showToast('Documento eliminado correctamente');
      currentConfig.recent_conversions = data.recent_conversions || [];
      renderRecentList(currentConfig.recent_conversions);
      if (lastGeneratedResult && (lastGeneratedResult.filename === filename || lastGeneratedResult.file_path === filePath)) {
        document.getElementById('resultCard').style.display = 'none';
        lastGeneratedResult = null;
      }
    } else {
      showToast('Error: ' + (data.error || 'No se pudo eliminar'));
    }
  } catch (err) {
    console.error('Error al eliminar:', err);
    showToast('Error de comunicación al eliminar documento');
  }
}

function updateHeroButtons() {
  const pasteBtn = document.getElementById('pasteAndConvertBtn');
  const convertBtn = document.getElementById('convertBtn');
  if (!pasteBtn || !convertBtn) return;

  if (activeTab === 'file') {
    // Primary button converts the file
    pasteBtn.onclick = performConversion;
    pasteBtn.title = "Convierte el archivo seleccionado a documento HTML";
    const mainLabel = pasteBtn.querySelector('.btn-hero-main-label');
    if (mainLabel) {
      mainLabel.innerHTML = `
        <span style="font-size: 1.05rem;">📄⚡</span>
        <span>Convertir Archivo</span>
      `;
    }
    const subLabel = pasteBtn.querySelector('.btn-hero-sub-label');
    if (subLabel) {
      subLabel.textContent = "Convierte el .md seleccionado";
    }

    // Secondary button offers paste & convert
    convertBtn.onclick = pasteAndConvert;
    convertBtn.title = "Pega el portapapeles y compila a HTML";
    const secMainLabel = convertBtn.querySelector('.btn-hero-main-label');
    if (secMainLabel) {
      secMainLabel.innerHTML = `
        <span>📋</span>
        <span>Pegar y Convertir</span>
      `;
    }
    const secSubLabel = convertBtn.querySelector('.btn-hero-sub-label');
    if (secSubLabel) {
      secSubLabel.textContent = "(Portapapeles)";
    }
  } else {
    // Text tab: Primary button is Paste & Convert
    pasteBtn.onclick = pasteAndConvert;
    pasteBtn.title = "Pega el portapapeles y compila a HTML en un solo clic (Ctrl+Shift+V)";
    const mainLabel = pasteBtn.querySelector('.btn-hero-main-label');
    if (mainLabel) {
      mainLabel.innerHTML = `
        <span style="font-size: 1.05rem;">📋⚡</span>
        <span>Pegar y Convertir</span>
      `;
    }
    const subLabel = pasteBtn.querySelector('.btn-hero-sub-label');
    if (subLabel) {
      subLabel.textContent = "1 Clic · Portapapeles (Ctrl+Shift+V)";
    }

    // Secondary button converts current textarea
    convertBtn.onclick = performConversion;
    convertBtn.title = "Convierte el texto actual";
    const secMainLabel = convertBtn.querySelector('.btn-hero-main-label');
    if (secMainLabel) {
      secMainLabel.innerHTML = `
        <span>⚡</span>
        <span>Convertir Actual</span>
      `;
    }
    const secSubLabel = convertBtn.querySelector('.btn-hero-sub-label');
    if (secSubLabel) {
      secSubLabel.textContent = "(Ctrl + Enter)";
    }
  }
}

function switchTab(tab) {
  activeTab = tab;
  document.getElementById('tabTextBtn').classList.toggle('active', tab === 'text');
  document.getElementById('tabFileBtn').classList.toggle('active', tab === 'file');
  document.getElementById('tabTextContent').classList.toggle('active', tab === 'text');
  document.getElementById('tabFileContent').classList.toggle('active', tab === 'file');
  updateHeroButtons();
}

async function toggleAutoOpen() {
  const isChecked = document.getElementById('autoOpenToggle').checked;
  currentConfig.auto_open = isChecked;
  await fetch('/api/config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ auto_open: isChecked })
  });
  showToast(isChecked ? 'Abrir automáticamente: ACTIVADO' : 'Abrir automáticamente: DESACTIVADO');
}

async function toggleCloseOnConvert() {
  const isChecked = document.getElementById('closeOnConvertToggle').checked;
  currentConfig.close_on_convert = isChecked;
  await fetch('/api/config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ close_on_convert: isChecked })
  });
  showToast(isChecked ? 'Cerrar ventana al convertir: ACTIVADO' : 'Cerrar ventana al convertir: DESACTIVADO');
}

async function closeAppWindow() {
  try {
    await fetch('/api/close-window', { method: 'POST' });
  } catch (e) {
    console.warn('Aviso cerrando ventana vía API:', e);
  }
  try {
    window.close();
  } catch (e) {}
}

async function browseFolder() {
  try {
    const res = await fetch('/api/browse-folder', { method: 'POST' });
    const data = await res.json();
    if (data.chosen_path) {
      currentConfig.root_dir = data.chosen_path;
      document.getElementById('currentDirPath').textContent = data.chosen_path;
      document.getElementById('currentDirPath').title = data.chosen_path;
      showToast('Directorio raíz actualizado');
      loadConfig();
    }
  } catch (e) {
    console.error('Error seleccionando carpeta:', e);
  }
}

function openCurrentFolder() {
  fetch('/api/open-folder', { method: 'POST' });
}

function openLogs() {
  fetch('/api/open-logs', { method: 'POST' }).catch(() => {});
  showToast('Abriendo debug_log.txt...');
}

async function browseFile() {
  try {
    const res = await fetch('/api/browse-file', { method: 'POST' });
    const data = await res.json();
    if (data.file_path) {
      selectedFilePath = data.file_path;
      document.getElementById('selectedFileName').textContent = data.filename;
      document.getElementById('selectedFileBadge').style.display = 'flex';
      document.getElementById('dropzone').style.display = 'none';
      updateHeroButtons();
    }
  } catch (e) {
    console.error('Error seleccionando archivo:', e);
  }
}

function clearSelectedFile() {
  selectedFilePath = '';
  document.getElementById('selectedFileBadge').style.display = 'none';
  document.getElementById('dropzone').style.display = 'flex';
}

async function getClipboardText() {
  try {
    const res = await fetch('/api/clipboard');
    if (res.ok) {
      const data = await res.json();
      if (data && typeof data.text === 'string') {
        return data.text;
      }
    }
  } catch (err) {
    console.warn('Backend clipboard endpoint no disponible, recurriendo a Web API:', err);
  }

  if (navigator.clipboard && navigator.clipboard.readText) {
    return await navigator.clipboard.readText();
  }

  throw new Error('No se pudo acceder al portapapeles');
}

async function pasteClipboard() {
  try {
    const text = await getClipboardText();
    if (text && text.trim()) {
      const ta = document.getElementById('markdownInput');
      ta.value = text;
      updateCounters();
      showToast('Texto pegado del portapapeles');
    } else {
      showToast('⚠️ El portapapeles está vacío o no contiene texto');
    }
  } catch (e) {
    showToast('Usa Ctrl + V para pegar');
  }
}

function clearTextarea() {
  document.getElementById('markdownInput').value = '';
  updateCounters();
}

function updateCounters() {
  const val = document.getElementById('markdownInput').value;
  const chars = val.length;
  const words = val.trim() ? val.trim().split(/\s+/).length : 0;
  document.getElementById('charCount').textContent = `${chars} caracteres · ${words} palabras`;
}

async function pasteAndConvert() {
  let text = '';
  try {
    text = await getClipboardText();
  } catch (err) {
    console.error('Error al leer portapapeles:', err);
    showToast('⚠️ No se pudo leer el portapapeles. Usa Ctrl+V y presiona Convertir');
    return;
  }

  if (!text || !text.trim()) {
    showToast('⚠️ El portapapeles está vacío o no contiene texto');
    return;
  }

  if (activeTab !== 'text') {
    switchTab('text');
  }

  const ta = document.getElementById('markdownInput');
  ta.value = text;
  updateCounters();

  showToast('⚡ Pegando del portapapeles y convirtiendo...');
  await performConversion();
}

async function performConversion() {
  const pasteBtn = document.getElementById('pasteAndConvertBtn');
  const convertBtn = document.getElementById('convertBtn');
  const customTitle = document.getElementById('customTitleInput').value.trim();

  let payload = {
    custom_title: customTitle,
    auto_open: document.getElementById('autoOpenToggle').checked
  };

  if (activeTab === 'file') {
    if (!selectedFilePath) {
      showToast('Por favor selecciona un archivo .md');
      return;
    }
    payload.file_path = selectedFilePath;
  } else {
    const text = document.getElementById('markdownInput').value.trim();
    if (!text) {
      showToast('Por favor escribe o pega texto Markdown');
      return;
    }
    payload.text = text;
  }

  [pasteBtn, convertBtn].forEach(b => {
    if (b) {
      b.style.opacity = '0.6';
      b.style.pointerEvents = 'none';
    }
  });

  try {
    console.log('[App] Enviando Markdown al motor para conversión...');
    const res = await fetchWithRetry('/api/convert', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }, 2, 350, 15000);

    const data = await res.json();
    if (data.success) {
      lastGeneratedResult = data;
      document.getElementById('resultDocTitle').textContent = data.title;
      document.getElementById('resultPath').textContent = data.file_path;
      document.getElementById('resultCard').style.display = 'flex';
      showToast('¡HTML generado exitosamente!');
      const closeToggle = document.getElementById('closeOnConvertToggle');
      if (closeToggle && closeToggle.checked) {
        setTimeout(closeAppWindow, 250);
      }
      loadConfig();
    } else {
      showToast('Error: ' + (data.error || 'No se pudo convertir'));
    }
  } catch (err) {
    console.error('Error al convertir:', err);
    if (err && err.name === 'AbortError') {
      showToast('⚠️ Tiempo de espera agotado con el motor (Timeout). Revisa Ver Logs');
    } else {
      showToast('⚠️ Error de comunicación con el motor. Revisa Ver Logs');
    }
  } finally {
    [pasteBtn, convertBtn].forEach(b => {
      if (b) {
        b.style.opacity = '1';
        b.style.pointerEvents = 'auto';
      }
    });
  }
}

function openGeneratedDoc() {
  if (lastGeneratedResult) {
    openUrl(lastGeneratedResult.file_url);
  }
}

function copyGeneratedLink() {
  if (lastGeneratedResult) {
    copyText(lastGeneratedResult.file_url, 'Enlace copiado al portapapeles');
  }
}

function openIndexInBrowser() {
  fetch('/api/open-index', { method: 'POST' });
}

function openUrl(url) {
  fetch('/api/open-file', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url: url })
  });
}

function copyText(str, msg) {
  navigator.clipboard.writeText(str).then(() => {
    showToast(msg || 'Copiado al portapapeles');
  });
}

const dropzone = document.getElementById('dropzone');
if (dropzone) {
  ['dragenter', 'dragover'].forEach(name => {
    dropzone.addEventListener(name, (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    });
  });
  ['dragleave', 'drop'].forEach(name => {
    dropzone.addEventListener(name, (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
    });
  });
  dropzone.addEventListener('drop', (e) => {
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const file = files[0];
      const reader = new FileReader();
      reader.onload = (re) => {
        document.getElementById('markdownInput').value = re.target.result;
        switchTab('text');
        updateCounters();
        showToast(`Cargado contenido de ${file.name}`);
      };
      reader.readAsText(file, 'UTF-8');
    }
  });
}

// Window-level Drag & Drop support
window.addEventListener('dragover', (e) => {
  e.preventDefault();
});
window.addEventListener('drop', (e) => {
  e.preventDefault();
  const files = e.dataTransfer && e.dataTransfer.files;
  if (files && files.length > 0) {
    const file = files[0];
    const reader = new FileReader();
    reader.onload = (re) => {
      document.getElementById('markdownInput').value = re.target.result;
      switchTab('text');
      updateCounters();
      showToast(`Cargado contenido de ${file.name}`);
    };
    reader.readAsText(file, 'UTF-8');
  }
});

document.addEventListener('keydown', (e) => {
  if ((e.ctrlKey || e.metaKey) && e.shiftKey && (e.key === 'V' || e.key === 'v')) {
    e.preventDefault();
    pasteAndConvert();
  } else if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    e.preventDefault();
    performConversion();
  }
});

const HEARTBEAT_INTERVAL_MS = 3500;
const HEARTBEAT_RETRY_MS = 1500;
const HEARTBEAT_TIMEOUT_MS = 6000;
// Tiempo sin latidos exitosos antes de mostrar "Reconectando..." (tolera reposo, suspensión y throttling)
const RECONNECT_GRACE_MS = 20000;

let heartbeatWorker = null;
let heartbeatInFlight = false;
let heartbeatTimer = null;
let engineIsActive = true;
let lastHeartbeatOkAt = Date.now();

function updateEngineStatus(isActive) {
  const text = document.getElementById('engineStatus');
  const dot = document.querySelector('.status-dot');
  const capsule = document.querySelector('.status-capsule');
  if (isActive) {
    if (text) text.textContent = 'Motor Activo';
    if (capsule) {
      capsule.style.background = 'var(--success-surface)';
      capsule.style.color = 'var(--success)';
      capsule.style.borderColor = 'rgba(16, 185, 129, 0.25)';
    }
    if (dot) {
      dot.style.background = 'var(--success)';
      dot.style.boxShadow = '0 0 8px var(--success)';
    }
  } else {
    if (text) text.textContent = 'Reconectando...';
    if (capsule) {
      capsule.style.background = 'rgba(239, 68, 68, 0.14)';
      capsule.style.color = 'var(--danger)';
      capsule.style.borderColor = 'rgba(239, 68, 68, 0.25)';
    }
    if (dot) {
      dot.style.background = 'var(--danger)';
      dot.style.boxShadow = '0 0 8px var(--danger)';
    }
  }
}

function markHeartbeat(ok) {
  if (ok) {
    lastHeartbeatOkAt = Date.now();
    if (!engineIsActive) {
      engineIsActive = true;
      updateEngineStatus(true);
      loadConfig();
    }
    return;
  }
  if (engineIsActive && Date.now() - lastHeartbeatOkAt > RECONNECT_GRACE_MS) {
    engineIsActive = false;
    updateEngineStatus(false);
  }
}

function scheduleNextHeartbeat(delayMs) {
  clearTimeout(heartbeatTimer);
  heartbeatTimer = setTimeout(sendHeartbeat, delayMs);
}

async function sendHeartbeat() {
  if (heartbeatInFlight) return;
  heartbeatInFlight = true;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), HEARTBEAT_TIMEOUT_MS);
  let ok = false;
  try {
    const res = await fetch('/api/heartbeat', {
      method: 'POST',
      cache: 'no-store',
      signal: controller.signal
    });
    ok = res.ok;
  } catch (err) {
    ok = false;
  } finally {
    clearTimeout(timeoutId);
    heartbeatInFlight = false;
  }
  markHeartbeat(ok);
  scheduleNextHeartbeat(ok ? HEARTBEAT_INTERVAL_MS : HEARTBEAT_RETRY_MS);
}

// Tras reposo, bloqueo de pantalla o suspensión el navegador congela/ralentiza los temporizadores:
// se concede un nuevo periodo de gracia y se verifica el motor de inmediato.
function wakeUpHeartbeat() {
  if (engineIsActive) {
    lastHeartbeatOkAt = Date.now();
  }
  sendHeartbeat();
}

try {
  // Las URLs relativas no se resuelven dentro de un Worker creado desde Blob: se usa el origen absoluto.
  const heartbeatUrl = `${location.origin}/api/heartbeat`;
  const workerCode = `
    const URL_HB = ${JSON.stringify(heartbeatUrl)};
    async function beat() {
      const controller = new AbortController();
      const t = setTimeout(() => controller.abort(), ${HEARTBEAT_TIMEOUT_MS});
      try {
        const res = await fetch(URL_HB, { method: 'POST', cache: 'no-store', signal: controller.signal });
        self.postMessage({ ok: res.ok });
      } catch (e) {
        self.postMessage({ ok: false });
      } finally {
        clearTimeout(t);
      }
    }
    setInterval(beat, ${HEARTBEAT_INTERVAL_MS});
  `;
  const blob = new Blob([workerCode], { type: 'application/javascript' });
  heartbeatWorker = new Worker(URL.createObjectURL(blob));
  heartbeatWorker.onmessage = (ev) => markHeartbeat(!!(ev.data && ev.data.ok));
} catch (e) {
  console.warn('Web Worker no disponible, operando en hilo principal:', e);
}

sendHeartbeat();

window.addEventListener('focus', () => {
  wakeUpHeartbeat();
  loadConfig();
});
window.addEventListener('online', wakeUpHeartbeat);
window.addEventListener('pageshow', wakeUpHeartbeat);
document.addEventListener('resume', wakeUpHeartbeat);
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible') {
    wakeUpHeartbeat();
    loadConfig();
  }
});

function notifyShutdown() {
  try {
    const payload = JSON.stringify({ reason: 'window_unload' });
    if (navigator.sendBeacon) {
      navigator.sendBeacon('/api/shutdown', payload);
    } else {
      fetch('/api/shutdown', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: payload,
        keepalive: true
      }).catch(() => {});
    }
  } catch (e) {}
}
window.addEventListener('pagehide', (e) => {
  // Congelación/bfcache (persisted) no es un cierre real de la ventana
  if (e && e.persisted) return;
  notifyShutdown();
});
window.addEventListener('beforeunload', notifyShutdown);

function adjustWindowSize() {
  const sw = window.screen.availWidth || window.screen.width;
  const sh = window.screen.availHeight || window.screen.height;
  if (!sw || !sh) return;

  let targetW, targetH;
  if (sw >= 1600) {
    targetW = 750;
    targetH = Math.min(680, Math.round(sh * 0.68));
  } else {
    targetW = Math.max(680, Math.min(1280, Math.round(sw * 0.85)));
    targetH = Math.max(560, Math.min(760, Math.round(sh * 0.86)));
  }
  const posX = Math.max(0, Math.round((sw - targetW) / 2));
  const posY = Math.max(0, Math.round((sh - targetH) / 2));

  try {
    window.resizeTo(targetW, targetH);
    window.moveTo(posX, posY);
  } catch (e) {}

  fetch('/api/adjust-window', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ screen_w: sw, screen_h: sh })
  }).catch(() => {});
}

adjustWindowSize();
loadConfig();
updateCounters();
