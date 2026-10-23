# Markdown to HTML — Desktop Application (Apple OLED Dark)

Aplicación de escritorio nativa para Windows, ultra-rápida (<20ms), ligera y diseñada con los principios de **Apple Design (WWDC)**.

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

---

## 🎨 Especificaciones de Diseño (Apple HIG)

- Paleta OLED Dark: fondo `#000000`, tarjetas `#141416`, bordes con reflejo de luz sutil.
- Materiales translúcidos (`backdrop-filter: blur(20px)`).
- Respuesta física inmediata en pointer-down (`transform: scale(0.97)` en botones).
- Tipografía SF Pro / system-ui con tracking óptico negativo en títulos grandes.
