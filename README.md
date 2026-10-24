# Markdown to HTML — Desktop Application (Terracotta Copper & Smoked Charcoal Mate)

Aplicación de escritorio nativa para Windows, ultra-rápida (<20ms), ligera y diseñada con una cuidada estética mate de **Terracota Cobre & Carbón Ahumado (Terracotta & Smoked Charcoal)** basada en principios de diseño industrial de alta gama.

Convierte texto Markdown o archivos `.md` en documentos HTML autónomos y profesionales, organizados en una biblioteca local con índice cronológico y navegación cruzada.

---

## 🚀 Inicio Rápido

### En esta laptop:
- **Doble clic en el acceso directo del Escritorio:** `Markdown to HTML`
- **O desde el Menú Inicio:** Busca `Markdown to HTML` y presiona Enter.
- **O ejecutando directamente:** Doble clic en `launch.vbs` (inicio 100% silencioso) o `run.bat`.

### En cualquier otra laptop con Windows:
1. Copia toda la carpeta `MarkdownToHTML_App` a donde desees.
2. Haz clic derecho en `install_shortcuts.ps1` -> **Ejecutar con PowerShell** (o ejecuta `run.bat`).
3. ¡Listo! Tendrás tu icono en el escritorio y podrás usar la app sin instalar nada más.

---

## 🌟 Características Principales

1. **Ultraligera y Cero Bloatware:**
   - No requiere Electron ni librerías pesadas de `pip`.
   - Utiliza el modo ventana de Microsoft Edge / Chrome preinstalado en Windows.
   - Cierre automático: el proceso en segundo plano se apaga solo al cerrar la ventana.

2. **Entrada Flexible:**
   - **Pega tu texto Markdown:** Área de edición con conteo de palabras/caracteres, botón de pegar y atajo de teclado (`Ctrl + Enter`).
   - **Carga desde archivo:** Arrastra y suelta (Drag & Drop) o examina archivos `.md`, `.markdown` o `.txt`.

3. **Acciones Inmediatas al Convertir:**
   - **Abrir en Navegador:** Abre la página directamente en tu navegador predeterminado.
   - **Copiar Enlace:** Copia al instante la ruta/enlace `file:///...` al portapapeles.
   - **Toggle "Abrir automáticamente":** Decide en cualquier momento si quieres que se abra de inmediato al convertir o solo cuando tú presiones el botón.

4. **Directorio Raíz Personalizable:**
   - Cambia la carpeta destino de los archivos en cualquier momento con el botón **📂 Cambiar Carpeta** (selector nativo de Windows).
   - Verificación defensiva continua: si la ruta no existe, la crea de inmediato de manera segura.

5. **Catálogo Cronológico (`index.html`) y Puntero (`latest.html`):**
   - Mantiene automáticamente un índice en la carpeta raíz ordenando los archivos desde el más nuevo hasta el más viejo.
   - Buscador en tiempo real dentro del índice para filtrar documentos por título o nombre.
   - Puntero automático `latest.html` que siempre abre el documento más nuevo creado.

6. **Navegación Cruzada en Cada Página:**
   - Cada HTML generado incluye una barra superior flotante con botones directos:
     - `[ 📁 Índice de Documentos ]` (abre `index.html`)
     - `[ ⚡ Más Reciente ]` (abre `latest.html`)
     - `[ 🌓 Modo Claro/Oscuro ]` (alternador interactivo)

7. **Jerarquía Visual de Listas y Sublistas:**
   - Soporte completo para listas ordenadas (`1.`, `2.`), no ordenadas (`-`, `*`) y checklists (`- [ ]`, `- [x]`).
   - Sangría progresiva a la derecha para sublistas anidadas con viñetas concéntricas (`disc` -> `circle` -> `square`).
   - Enlaces intra-documento con navegación fluida sin recarga.

8. **Diseño Adaptativo y Tamaño Dinámico de Ventana:**
   - **Inicio inteligente según pantalla:** Ventana compacta y pequeña en monitores de escritorio para facilitar la multitarea, y amplia/espaciosa en laptops.
   - **Interfaz 100% responsiva:** Tipografía fluida con funciones `clamp()`, botones adaptativos en cuadrículas dinámicas y soporte desde 360px hasta 4K.

---

## 🎨 Especificaciones de Diseño (Terracotta Copper & Smoked Charcoal Mate)

- **Paleta Smoked Charcoal Mate:** Fondo negro humo profundo `#0b0a0a`, tarjetas en carbón tostado `#141312`, superficie elevada `#1c1a19` y bordes con reflejo reflectante cálido (`rgba(220, 180, 150, 0.08)`).
- **Acento Cobre Terracota:** Botones y elementos interactivos en cobre mate `#d97736` con gradiente `linear-gradient(180deg, #d97736 0%, #b85b1e 100%)` y hover `#e58746`.
- **Tipografía y Legibilidad:** Texto en pergamino suave anti-fatiga `#f5ede6` y titanio tostado `#a6988f`.
- **Materiales ahumados:** Fondos translúcidos con `backdrop-filter: blur(20px)`.
- **Respuesta táctil y micro-animaciones:** Curvas de resorte `cubic-bezier(0.16, 1, 0.3, 1)` y retroalimentación táctil `transform: scale(0.97)`.

---

## 🧪 Pruebas Automatizadas y Calidad de Código

La aplicación cuenta con una suite integral de 85 pruebas unitarias, de integración, de seguridad y de geometría, sin dependencias externas:

```powershell
# Ejecutar suite integral completa (85 tests con métricas en tiempo real):
python run_tests.py

# O ejecutar verificación rápida de humo (9 checks):
python verify_app.py
```

### Módulos de Prueba (`tests/`):
- **`tests/test_md_engine.py` (45 tests):** Compilador léxico y sintáctico, tokens del tema terracota cobre, callouts GitHub, tablas con alineación, atajos `[[kbd:...]]`, jerarquía de listas anidadas, badges de estado, slugify y catálogo cronológico.
- **`tests/test_app_api.py` (19 tests):** API REST del servidor HTTP local sobre loopback real (`127.0.0.1`), códigos de estado HTTP, endpoints GET/POST, validación y manejo de errores.
- **`tests/test_window_geometry.py` (7 tests):** Detección de pantallas de escritorio vs. laptops, dimensionamiento adaptativo, límites mínimos y centrado nativo.
- **`tests/test_config_and_history.py` (9 tests):** Persistencia de configuración, auto-recarga de documentos existentes al abrir la app, recuperación ante JSON corrupto, límite estricto de 10 elementos e higiene de archivos fantasma.
- **`tests/test_security.py` (5 tests):** Prevención de Path Traversal en `/assets/`, protección de archivos del sistema e `index.html`/`latest.html` contra eliminación y sanitización XSS.

---

## 🌿 Flujo de Trabajo Git Flow y Contribución

El desarrollo sigue el estándar de ramas **Git Flow** y **Conventional Commits**:
- Consulta la guía completa en [GIT_FLOW.md](file:///c:/General/MarkdownToHTML_App/GIT_FLOW.md).
- Ramas principales: `master` (producción) y `develop` (integración).
- Ramas de trabajo: `feature/*`, `bugfix/*`, `release/*`, `hotfix/*`, `test/*`.
- Toda contribución debe pasar el 100% de la suite de pruebas antes de integrarse.


