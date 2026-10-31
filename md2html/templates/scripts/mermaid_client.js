function toggleMermaidSource(id, btn) {
  const srcEl = document.getElementById('source-' + id);
  if (!srcEl) return;
  const isHidden = srcEl.style.display === 'none';
  srcEl.style.display = isHidden ? 'block' : 'none';
  const label = btn.querySelector('span');
  if (label) label.textContent = isHidden ? 'Ocultar código' : 'Ver código';
}

function copyMermaidSource(id, btn) {
  const rawEl = document.getElementById('raw-' + id);
  if (!rawEl) return;
  navigator.clipboard.writeText(rawEl.textContent.trim()).then(() => {
    const label = btn.querySelector('span');
    const orig = label ? label.textContent : '';
    btn.classList.add('copied');
    if (label) label.textContent = '✓ Copiado';
    setTimeout(() => {
      btn.classList.remove('copied');
      if (label) label.textContent = orig;
    }, 2000);
  }).catch(err => {
    console.error('Error al copiar Mermaid:', err);
  });
}

function escapeHtml(str) {
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

async function renderMermaidDiagrams() {
  if (typeof mermaid === 'undefined') return;
  const isDark = !document.documentElement.classList.contains('light');
  try {
    mermaid.initialize({
      startOnLoad: false,
      theme: isDark ? 'dark' : 'default',
      securityLevel: 'loose',
      fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", "Segoe UI", Roboto, sans-serif'
    });
  } catch (e) {
    console.error('Mermaid init error:', e);
  }

  const blocks = document.querySelectorAll('.mermaid-block');
  for (let i = 0; i < blocks.length; i++) {
    const block = blocks[i];
    const diagId = block.id.replace('block-', '');
    const rawEl = document.getElementById('raw-' + diagId);
    const renderEl = document.getElementById('render-' + diagId);
    if (!rawEl || !renderEl) continue;

    const rawCode = rawEl.textContent.trim();
    const uniqueId = 'svg-' + diagId + '-' + (isDark ? 'dark' : 'light') + '-' + Math.floor(Math.random() * 100000);
    try {
      const res = await mermaid.render(uniqueId, rawCode);
      renderEl.innerHTML = res.svg;
      if (res.bindFunctions) {
        res.bindFunctions(renderEl);
      }
    } catch (err) {
      console.error('Mermaid render error for ' + diagId + ':', err);
      renderEl.innerHTML = '<div class="mermaid-error"><strong>⚠️ Aviso de sintaxis Mermaid:</strong> ' +
        escapeHtml(err.message || 'Error en la definición del diagrama') +
        '</div>';
      const srcEl = document.getElementById('source-' + diagId);
      if (srcEl) srcEl.style.display = 'block';
      const toggleBtn = block.querySelector('.toggle-source-btn span');
      if (toggleBtn) toggleBtn.textContent = 'Ocultar código';
    }
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', renderMermaidDiagrams);
} else {
  renderMermaidDiagrams();
}
