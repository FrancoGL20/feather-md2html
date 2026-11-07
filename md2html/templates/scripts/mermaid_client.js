function toggleMermaidSource(id, btn) {
  const srcEl = document.getElementById('source-' + id);
  if (!srcEl) return;
  const isHidden = srcEl.style.display === 'none';
  srcEl.style.display = isHidden ? 'block' : 'none';
  const label = btn.querySelector('span');
  if (label) label.textContent = isHidden ? 'Ocultar código' : 'Ver código';
}

function toggleMermaidExportMenu(id, event) {
  if (event) {
    event.stopPropagation();
  }
  const menu = document.getElementById('export-menu-' + id);
  if (!menu) return;
  const isShown = menu.classList.contains('show');
  closeAllMermaidExportMenus();
  if (!isShown) {
    menu.classList.add('show');
  }
}

function closeAllMermaidExportMenus() {
  document.querySelectorAll('.mermaid-export-menu.show').forEach((m) => {
    m.classList.remove('show');
  });
}

document.addEventListener('click', closeAllMermaidExportMenus);
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closeAllMermaidExportMenus();
});

function triggerDownload(url, filename) {
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, 2000);
}

function convertForeignObjectsToSvgText(svgRoot) {
  const fos = Array.from(svgRoot.querySelectorAll('foreignObject'));
  for (const fo of fos) {
    const parent = fo.parentNode;
    if (!parent) continue;
    const w = parseFloat(fo.getAttribute('width') || '100');
    const h = parseFloat(fo.getAttribute('height') || '30');
    const x = parseFloat(fo.getAttribute('x') || '0');
    const y = parseFloat(fo.getAttribute('y') || '0');

    // Extract text lines cleanly, handling <br> and paragraph divisions
    const cloneFO = fo.cloneNode(true);
    const brs = cloneFO.querySelectorAll('br');
    brs.forEach((b) => b.replaceWith('\n'));

    let lines = (cloneFO.textContent || '')
      .split('\n')
      .map((l) => l.trim())
      .filter(Boolean);
    if (lines.length === 0) lines = [''];

    // Read computed style or inline style for accurate colors and typography
    const targetEl = fo.querySelector('span') || fo.querySelector('p') || fo.querySelector('div') || fo;
    let color = '#f8fafc';
    let fontSize = '14px';
    let fontWeight = '500';

    if (window.getComputedStyle) {
      try {
        const computed = window.getComputedStyle(targetEl);
        if (computed) {
          if (computed.color && computed.color !== 'rgba(0, 0, 0, 0)') color = computed.color;
          if (computed.fontSize) fontSize = computed.fontSize;
          if (computed.fontWeight) fontWeight = computed.fontWeight;
        }
      } catch (e) {
        // Fallback to default colors
      }
    }

    const textEl = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    textEl.setAttribute('x', (x + w / 2).toString());
    textEl.setAttribute('text-anchor', 'middle');
    textEl.setAttribute('dominant-baseline', 'central');
    textEl.setAttribute('fill', color);
    textEl.setAttribute('font-size', fontSize);
    textEl.setAttribute('font-weight', fontWeight);
    textEl.setAttribute('font-family', '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif');

    const fsNum = parseFloat(fontSize) || 14;
    const lineHeight = fsNum * 1.35;
    const lineCount = lines.length;
    const startY = y + (h / 2) - ((lineCount - 1) * lineHeight / 2);
    textEl.setAttribute('y', startY.toString());

    if (lines.length === 1) {
      textEl.textContent = lines[0];
    } else {
      lines.forEach((line, idx) => {
        const tspan = document.createElementNS('http://www.w3.org/2000/svg', 'tspan');
        tspan.setAttribute('x', (x + w / 2).toString());
        tspan.setAttribute('dy', idx === 0 ? '0' : lineHeight.toString());
        tspan.textContent = line;
        textEl.appendChild(tspan);
      });
    }

    parent.replaceChild(textEl, fo);
  }
}

function exportMermaidDiagram(id, format, action) {
  closeAllMermaidExportMenus();
  const renderEl = document.getElementById('render-' + id);
  if (!renderEl) return;
  const svgEl = renderEl.querySelector('svg');
  if (!svgEl) {
    alert('El diagrama aún no ha terminado de renderizarse.');
    return;
  }

  const isLight = document.documentElement.classList.contains('light');
  const bgColor = isLight ? '#ffffff' : '#111114';

  const clonedSvg = svgEl.cloneNode(true);

  let width = 800;
  let height = 600;
  const viewBox = svgEl.getAttribute('viewBox');
  if (viewBox) {
    const parts = viewBox.trim().split(/[\s,]+/).map(Number);
    if (parts.length >= 4 && parts[2] > 0 && parts[3] > 0) {
      width = parts[2];
      height = parts[3];
    }
  } else {
    const bbox = svgEl.getBoundingClientRect();
    if (bbox.width && bbox.height) {
      width = bbox.width;
      height = bbox.height;
    }
  }

  // Convert foreignObjects to native SVG text to prevent canvas tainting (SecurityError)
  convertForeignObjectsToSvgText(clonedSvg);

  clonedSvg.setAttribute('width', width);
  clonedSvg.setAttribute('height', height);
  if (viewBox) {
    clonedSvg.setAttribute('viewBox', viewBox);
  } else {
    clonedSvg.setAttribute('viewBox', '0 0 ' + width + ' ' + height);
  }
  if (!clonedSvg.getAttribute('xmlns')) {
    clonedSvg.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
  }

  const bgRect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
  bgRect.setAttribute('width', '100%');
  bgRect.setAttribute('height', '100%');
  bgRect.setAttribute('fill', bgColor);
  clonedSvg.insertBefore(bgRect, clonedSvg.firstChild);

  const serializer = new XMLSerializer();
  const svgXml = serializer.serializeToString(clonedSvg);

  const cleanTitle = (document.title || 'diagrama')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9_-]/g, '_')
    .replace(/_+/g, '_')
    .replace(/^_+|_+$/g, '')
    .substring(0, 40) || 'diagrama';
  const filename = cleanTitle + '-' + id + '.' + format;

  if (format === 'svg') {
    const blob = new Blob([svgXml], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    if (action === 'tab') {
      const win = window.open(url, '_blank');
      if (!win) triggerDownload(url, filename);
    } else {
      triggerDownload(url, filename);
    }
    return;
  }

  // Smart Adaptive Scaling with Cinema 4K Ultra-HD Clamping (Max 3840px width/height)
  // Ensures razor-sharp print and retina quality (< 25 ms) without 80 Megapixel bloat or memory lockups.
  let scale = 2;
  if (width < 800 && height < 800) {
    scale = 3;
  } else if (width > 2000 || height > 2000) {
    scale = 1.25;
  }
  const maxDim = Math.max(width * scale, height * scale);
  if (maxDim > 3840) {
    scale = 3840 / Math.max(width, height);
  }

  const targetWidth = Math.round(width * scale);
  const targetHeight = Math.round(height * scale);

  const canvas = document.createElement('canvas');
  canvas.width = targetWidth;
  canvas.height = targetHeight;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  ctx.fillStyle = bgColor;
  ctx.fillRect(0, 0, targetWidth, targetHeight);

  const svgBlob = new Blob([svgXml], { type: 'image/svg+xml;charset=utf-8' });
  const svgUrl = URL.createObjectURL(svgBlob);
  const img = new Image();

  img.onload = () => {
    try {
      ctx.drawImage(img, 0, 0, targetWidth, targetHeight);
      URL.revokeObjectURL(svgUrl);

      const mimeType = format === 'jpg' ? 'image/jpeg' : 'image/png';
      const quality = format === 'jpg' ? 0.92 : undefined;

      canvas.toBlob((blob) => {
        if (!blob) {
          alert('No se pudo generar la imagen ráster.');
          return;
        }
        const imgUrl = URL.createObjectURL(blob);
        if (action === 'tab') {
          const win = window.open(imgUrl, '_blank');
          if (!win) triggerDownload(imgUrl, filename);
        } else {
          triggerDownload(imgUrl, filename);
        }
      }, mimeType, quality);
    } catch (drawErr) {
      URL.revokeObjectURL(svgUrl);
      console.error('Error procesando canvas:', drawErr);
      alert('Error al exportar en formato ' + format.toUpperCase() + '. Puedes usar SVG (Vectorial) para máxima compatibilidad.');
    }
  };

  img.onerror = (e) => {
    URL.revokeObjectURL(svgUrl);
    console.error('Error al exportar diagrama:', e);
    alert('No se pudo convertir el diagrama a imagen en este navegador.');
  };

  img.src = svgUrl;
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

function autoRepairMermaid(code) {
  if (!code) return code;
  let repaired = code;
  // Repair reverse thick arrow with label: A <==|text| B -> A <==>|text| B
  repaired = repaired.replace(/<==\|/g, '<==>|');
  // Repair reverse thin arrow with label: A <--|text| B -> A <-->|text| B
  repaired = repaired.replace(/<--\|/g, '<-->|');
  // Repair reverse arrows with quoted strings: A <== "text" == B -> A <== "text" ==> B
  repaired = repaired.replace(/(<==\s*"[^"]*"\s*)==(?=\s)/g, '$1==>');
  repaired = repaired.replace(/(<--\s*"[^"]*"\s*)--(?=\s)/g, '$1-->');
  // Repair stand-alone invalid reverse arrows: A <== B -> A <==> B (when not followed by quote)
  repaired = repaired.replace(/(?<=\s)<==(?=\s+(?!"))/g, '<==>');
  repaired = repaired.replace(/(?<=\s)<--(?=\s+(?!"))/g, '<-->');
  return repaired;
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
      // Defensive Self-Healing: Attempt automatic repair of non-standard arrow syntax
      const repairedCode = autoRepairMermaid(rawCode);
      if (repairedCode !== rawCode) {
        try {
          const retryId = uniqueId + '-repaired';
          const res = await mermaid.render(retryId, repairedCode);
          renderEl.innerHTML = res.svg;
          if (res.bindFunctions) {
            res.bindFunctions(renderEl);
          }
          continue; // Successfully rendered via self-healing!
        } catch (retryErr) {
          console.warn('Mermaid self-healing retry failed for ' + diagId + ':', retryErr);
        }
      }

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
