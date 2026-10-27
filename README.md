# Markdown to HTML — Desktop Application

[![Platform: Windows](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-blue?logo=windows)](https://microsoft.com)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://python.org)
[![Zero Bloatware](https://img.shields.io/badge/Dependencies-Zero%20(Stdlib%20Only)-success)](#arquitectura-tecnica-y-principios-de-diseno)
[![Tests: 126 Passing](https://img.shields.io/badge/Tests-126%2F126%20Passing-brightgreen)](#pruebas-automatizadas-y-calidad-de-codigo)
[![Architecture: Chromium App Mode](https://img.shields.io/badge/Engine-Chromium%20App%20Mode-orange)](#arquitectura-tecnica-y-principios-de-diseno)
[![System Tray: Native Win32](https://img.shields.io/badge/System%20Tray-Native%20Win32-purple)](#integracion-en-el-system-tray-y-guardián-de-instancia-unica)

Aplicacion de escritorio nativa para Windows disenada para la transformacion ultra-rapida (<20 ms) de documentos Markdown a paginas HTML autonomas, responsivas y completamente portables. 

Construida bajo una filosofia estricta de **cero dependencias externas (Zero-Bloatware)**, renderizado acelerado por hardware mediante el modo aplicacion de Chromium y una interfaz visual basada en la paleta mate **Ambar Volcanico y Negro Obsidiana (Volcanic Amber & Deep Obsidian)**.

---

## Tabla de Contenidos

- [Vision General y Filosofia de Diseno](#vision-general-y-filosofia-de-diseno)
- [Caracteristicas Principales](#caracteristicas-principales)
- [Requisitos del Sistema](#requisitos-del-sistema)
- [Instalacion y Puesta en Marcha](#instalacion-y-puesta-en-marcha)
  - [Opcion 1: Instalador Rapido de 1 Clic (Recomendado)](#opcion-1-instalador-rapido-de-1-clic-recomendado)
  - [Opcion 2: Ejecucion Portatil (Standalone)](#opcion-2-ejecucion-portatil-standalone)
  - [Opcion 3: Clonacion con Git](#opcion-3-clonacion-con-git)
- [Guia de Migracion y Portabilidad a Otra PC](#guia-de-migracion-y-portabilidad-a-otra-pc)
- [Flujos de Trabajo y Uso](#flujos-de-trabajo-y-uso)
  - [Conversion de Texto y Portapapeles (Zero-Prompts)](#conversion-de-texto-y-portapapeles-zero-prompts)
  - [Conversion desde Archivo (Drag and Drop)](#conversion-desde-archivo-drag-and-drop)
  - [Diagramas Mermaid 100% Offline](#diagramas-mermaid-100-offline)
  - [Navegacion Cruzada y Biblioteca de Documentos](#navegacion-cruzada-y-biblioteca-de-documentos)
  - [Diagnostico y Visor de Registros](#diagnostico-y-visor-de-registros)
- [Arquitectura Tecnica y Principios de Diseno](#arquitectura-tecnica-y-principios-de-diseno)
  - [Filosofia Zero-Bloatware](#filosofia-zero-bloatware)
  - [Modo Aplicacion Chromium](#modo-aplicacion-chromium)
  - [Ciclo de Vida y Watchdog Defensivo](#ciclo-de-vida-y-watchdog-defensivo)
  - [Integracion en el System Tray y Guardian de Instancia Unica](#integracion-en-el-system-tray-y-guardian-de-instancia-unica)
  - [Integracion Win32 para Portapapeles](#integracion-win32-para-portapapeles)
  - [Cache Inteligente contra Bloqueo de Antivirus](#cache-inteligente-contra-bloqueo-de-antivirus)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Pruebas Automatizadas y Calidad de Codigo](#pruebas-automatizadas-y-calidad-de-codigo)
- [Desinstalacion](#desinstalacion)
- [Estandar de Contribucion y Git Flow](#estandar-de-contribucion-y-git-flow)
- [Licencia](#licencia)

---

## Vision General y Filosofia de Diseno

La mayoria de herramientas contemporaneas para previsualizar y convertir Markdown incorporan entornos pesados basados en Electron o requieren cadenas de herramientas complejas (`npm`, `pip`, compiladores C++ o servicios en la nube). Este proyecto resuelve esa problematica con una arquitectura hibrida minimalista:

1. **Velocidad Extrema (< 20 ms por documento):** El analizador lexico y sintactico procesa el contenido linea por linea en una sola pasada usando expresiones regulares compiladas sobre la biblioteca estandar de Python.
2. **Cero Dependencias de Paquetes (Zero-Bloatware):** No requiere `pip install`, ni entornos virtuales `venv`, ni `node_modules`. Todo el sistema funciona con modulos nativos incluidos en el runtime de Python (`http.server`, `urllib`, `json`, `ctypes`, `pathlib`, `re`, `socket`, `threading`).
3. **Ejecucion Nativa y Silenciosa:** Sin consolas negras de terminal visibles para el usuario final gracias a la integracion con `pythonw.exe`.
4. **Documentos Autocontenidos:** Cada archivo HTML generado es 100% independiente; incluye estilos CSS completos, tipografias del sistema, logica interactiva y, cuando corresponde, el runtime offline de Mermaid inyectado directamente. No requiere conexion a internet ni CDNs externos.

---

## Caracteristicas Principales

- **Bandeja del Sistema (System Tray) a 1 Clic:** Acceso instantaneo permanente desde el area de notificacion de Windows junto al reloj. Cierre de ventana optimizado (libera ~150 MB de Edge manteniendo Python en reposo en < 18 MB) y reapertura instantanea en < 200 ms.
- **Menu Contextual y Notificacion en Globo:** Opciones rapidas al dar clic derecho en la bandeja (*Abrir Markdown to HTML*, *Abrir Carpeta de Documentos*, *Ver Biblioteca*, *Salir completamente*) con notificacion informativa nativa de Windows.
- **Entrada Flexible:** Area de edicion con atajos rapidos (`Ctrl + Enter` para convertir, `Ctrl + Shift + V` para pegar y convertir), conteo de palabras y tiempo estimado de lectura en tiempo real.
- **Soporte Drag and Drop:** Arrastre de archivos `.md`, `.markdown` o `.txt` directamente sobre la interfaz o seleccion mediante el explorador nativo de Windows.
- **Acceso Directo al Portapapeles (Zero-Prompts):** Lectura instantanea de memoria via API Win32 a traves del backend, evitando los dialogos invasivos de solicitud de permisos del navegador.
- **Diagramas Mermaid Offline e Interactivos:** Deteccion automatica de bloques ```` ```mermaid ```` con renderizado SVG centrado, alternador de codigo fuente con un clic y boton para copiar la definicion con confirmacion visual.
- **Biblioteca Dinamica con Indice Cronologico (`index.html`):** Organizacion automatica de documentos desde el mas nuevo hasta el mas viejo, con buscador reactivo integrado en el cliente.
- **Puntero al Documento Mas Reciente (`latest.html`):** Redireccion automatica y enlace permanente para abrir de inmediato la ultima conversion generada.
- **Navegacion Cruzada Superior:** Todos los documentos generados integran una barra flotante para saltar al indice de documentos, al documento mas reciente o alternar entre tema oscuro y claro.
- **Resaltado de Sintaxis sin Dependencias:** Resaltado integrado para Python, JavaScript, JSON, PowerShell, Groovy, Gherkin y bloques `diff` (adiciones en verde y eliminaciones en rojo).
- **Tipografia y Tablas Responsivas:** Tablas con zebra striping y desplazamiento horizontal automatico, listas jerarquicas anidadas con sangria progresiva y marcadores jerarquicos (`disc` -> `circle` -> `square`).
- **Sistema de Diseno Volcanic Amber & Deep Obsidian:** Superficies de basalto mate (`#070708`, `#111114`, `#17181c`), acentos en ambar volcanico (`#f97316`), tipografia anti-fatiga y curvas de resorte naturales.

---

## Requisitos del Sistema

| Componente | Requisito Minimo | Recomendado | Notas |
| :--- | :--- | :--- | :--- |
| **Sistema Operativo** | Windows 10 (64-bit) | Windows 10 / 11 (64-bit) | Compatible con ediciones Home, Pro y Enterprise |
| **Python** | Python 3.8+ | Python 3.10+ | No requiere permisos de administrador ni `pip` |
| **Navegador** | Microsoft Edge | Microsoft Edge / Chrome | Preinstalado de forma nativa en Windows 10/11 |
| **PowerShell** | PowerShell 5.1+ | PowerShell 5.1+ | Integrado en el sistema operativo |
| **Espacio en Disco** | < 15 MB | < 20 MB | Incluyendo runtime de Mermaid y assets |

---

## Instalacion y Puesta en Marcha

### Opcion 1: Instalador Rapido de 1 Clic (Recomendado)

Disenado para usuarios finales y despliegue rapido en cualquier equipo con Windows:

1. Descarga o descomprime la carpeta del proyecto.
2. Ejecuta con doble clic **`instalar.bat`**.

**Acciones automaticas que realiza el instalador:**
- Verifica la presencia de Python en el sistema. Si no estuviera instalado, ofrece descargarlo e instalarlo automaticamente mediante `winget install -e --id Python.Python.3.12 --scope user`.
- Copia los archivos del programa a la ruta estandar de usuario: `%LOCALAPPDATA%\Programs\MarkdownToHTML_App` (no requiere permisos de Administrador ni dispara advertencias de UAC).
- Ejecuta `install_shortcuts.ps1` con `-ExecutionPolicy Bypass` para registrar accesos directos con el icono oficial (`assets/app_icon.ico`) en:
  - El **Escritorio**: `Markdown to HTML.lnk`
  - El **Menu Inicio**: buscando `Markdown to HTML`
- Configura el inicio silencioso con `pythonw.exe` (sin ventanas de terminal negras).

---

### Opcion 2: Ejecucion Portatil (Standalone)

Si prefieres utilizar la aplicacion sin instalarla en el sistema:

1. Ubica la carpeta `MarkdownToHTML_App` en cualquier unidad o directorio (ej. `C:\Herramientas\`, una memoria USB o tu carpeta de usuario).
2. Haz doble clic en **`launch.vbs`** para abrir la aplicacion de forma completamente silenciosa, o en **`run.bat`** para ejecucion rapida.
3. Si deseas crear los accesos directos apuntando a esa ubicacion fija, ejecuta en una terminal de PowerShell:
   ```powershell
   powershell.exe -ExecutionPolicy Bypass -File .\install_shortcuts.ps1
   ```

---

### Opcion 3: Clonacion con Git

Para desarrolladores o usuarios que mantendran la aplicacion sincronizada con el repositorio:

```powershell
# 1. Clonar el repositorio
git clone <URL_DEL_REPOSITORIO> MarkdownToHTML_App
cd MarkdownToHTML_App

# 2. Registrar accesos directos locales (opcional)
powershell -ExecutionPolicy Bypass -File .\install_shortcuts.ps1

# 3. Iniciar la aplicacion
# Opcion A (Silenciosa en segundo plano):
cscript //nologo launch.vbs

# Opcion B (Desde consola para ver salida de depuracion):
python app.py
```

---

## Guia de Migracion y Portabilidad a Otra PC

La aplicacion fue disenada para funcionar de forma inmediata al transferirse entre computadoras diferentes, sin provocar errores por rutas absolutas o historiales huerfanos.

### Principios de Portabilidad

1. **Resolucion de Rutas Dinamicas:**
   Todo el backend y el motor de compilacion resuelven sus rutas de manera relativa al directorio de ejecucion (`Path(__file__).resolve().parent`). La aplicacion puede ubicarse en cualquier disco o directorio sin alterar su funcionamiento.

2. **Aislamiento de Configuracion Local:**
   - El archivo `config.json` esta registrado en `.gitignore` para no filtrar rutas de desarrollo al repositorio.
   - Si `config.json` no existe al iniciar en una nueva maquina, el backend lo genera automaticamente a partir de `config.template.json`, estableciendo como directorio de salida por defecto la carpeta de descargas del usuario activo:
     ```text
     C:\Users\<UsuarioActual>\Downloads\Markdown_HTML_Library
     ```
   - Si la carpeta destino no existe fisicamente, el sistema la crea de forma segura en la primera ejecucion.

3. **Purga Automatica de Archivos Fantasma:**
   Si se transfiere un archivo `config.json` que contiene un historial de documentos generados en otra maquina, `app.py` valida la existencia fisica de cada archivo en disco al arrancar y depura silenciosamente aquellos que no existan, evitando enlaces rotos.

### Pasos para Migrar la Aplicacion en 10 Segundos

1. Comprime la carpeta `MarkdownToHTML_App` en un archivo `.zip` (o descargala del repositorio).
2. En la nueva computadora con Windows, descomprime la carpeta en la ubicacion deseada.
3. Haz doble clic en `instalar.bat` (o en `launch.vbs` para modo portable).
4. La aplicacion estara operativa de inmediato, lista para convertir y organizar documentos.

---

## Flujos de Trabajo y Uso

### Conversion de Texto y Portapapeles (Zero-Prompts)

1. **Pegar Contenido:**
   - Haz clic en **Pegar** para colocar el contenido del portapapeles en el area de texto.
   - O haz clic en **Pegar y Convertir** (o presiona `Ctrl + Shift + V`) para realizar ambas acciones en un solo paso.
   - La lectura se ejecuta a nivel de sistema operativo mediante la API Win32 del backend, por lo que el navegador **no mostrara advertencias emergentes solicitando permisos**.
2. **Convertir:**
   - Presiona el boton **Convertir Markdown a HTML** o utiliza el atajo `Ctrl + Enter`.
3. **Acciones Inmediatas:**
   - **Abrir Documento:** Muestra el archivo generado en tu navegador predeterminado.
   - **Copiar Enlace:** Copia al portapapeles la ruta `file:///...` lista para compartir o archivar.
   - **Abrir Carpeta:** Abre el Explorador de Windows posicionado en la carpeta de la biblioteca.

---

### Conversion desde Archivo (Drag and Drop)

1. Arrastra un archivo `.md`, `.markdown` o `.txt` y sueltalo dentro de la zona delimitada de la interfaz.
2. O haz clic en **Examinar Archivo (.md)** para elegirlo mediante el selector nativo de Windows.
3. Haz clic en **Convertir Archivo Seleccionado**.

---

### Diagramas Mermaid 100% Offline

Puedes incluir cualquier diagrama compatible con Mermaid encerrandolo en bloques de codigo con la etiqueta `mermaid`:

````markdown
```mermaid
graph TD
    A[Markdown Fuente] --> B(Compilador md_engine.py)
    B --> C{Tiene Mermaid?}
    C -- Si --> D[Inyectar Runtime Local assets/mermaid.min.js]
    C -- No --> E[Generar HTML Ultraligero < 50 KB]
    D --> F[Documento HTML Autonomo]
    E --> F
```
````

**Funcionalidades del bloque Mermaid generado:**
- **Tarjeta Responsiva:** Cabecera con titulo `DIAGRAMA MERMAID` e icono vectorial.
- **Visor de Codigo:** Boton **Ver codigo** / **Ocultar codigo** para inspeccionar la fuente sintactica sin salir del documento.
- **Boton Copiar:** Copia el codigo del diagrama al portapapeles con confirmacion visual (`✓ Copiado`).
- **Sincronizacion de Tema:** Al cambiar entre tema oscuro y claro en la barra de navegacion superior, los diagramas se recompilan en caliente con la paleta de colores adecuada.
- **Optimizacion de Tamano (Zero-Bloat):** Si el documento no incluye diagramas Mermaid, se omite por completo la inclusion del bundle JavaScript, preservando archivos ligeros (< 50 KB) y compilaciones en < 20 ms.

---

### Navegacion Cruzada y Biblioteca de Documentos

Cada pagina HTML generada incorpora una barra superior flotante:
- **Indice de Documentos (`./index.html`):** Abre el catalogo general ordenado cronologicamente, con buscador reactivo en vivo por titulo o nombre de archivo.
- **Mas Reciente (`./latest.html`):** Redirecciona instantaneamente al ultimo documento compilado.
- **Tema Claro / Oscuro:** Permite alternar la visualizacion segun las condiciones de iluminacion.

---

### Diagnostico y Visor de Registros

La aplicacion mantiene un registro de operacion defensivo en `debug_log.txt`:
- Puedes presionar el boton **Ver Logs** en la cabecera de la aplicacion para consultar en pantalla los eventos mas recientes del servidor.
- Haz clic en **Abrir archivo de log** para abrir `debug_log.txt` directamente en el Bloc de notas o editor predeterminado del sistema.

---

## Arquitectura Tecnica y Principios de Diseno

```mermaid
sequenceDiagram
    autonumber
    actor Usuario
    participant Acceso as Acceso Directo (.lnk)
    participant PythonW as pythonw.exe (Backend)
    participant Server as HTTP Server (127.0.0.1:51870)
    participant Edge as Microsoft Edge (--app)
    participant Engine as md_engine.py
    participant Disk as Biblioteca Local (HTMLs)

    Usuario->>Acceso: Doble clic
    Acceso->>PythonW: Ejecuta app.py en segundo plano
    PythonW->>Server: Inicia HTTPServer en puerto preferido 51870
    PythonW->>Edge: Lanza msedge.exe --app="http://127.0.0.1:51870"
    Edge->>Server: GET / (Carga ui/index.html)
    Server-->>Edge: Retorna SPA en tema Volcanic Amber
    Edge->>Server: POST /api/heartbeat (Cada 3.5s via Web Worker)

    Usuario->>Edge: Clic en "Pegar y Convertir"
    Edge->>Server: GET /api/clipboard (Win32 API directa)
    Server-->>Edge: Retorna texto del portapapeles sin permisos
    Edge->>Server: POST /api/convert {text, auto_open}
    Server->>Engine: convert_and_update_library()
    Engine->>Disk: Escribe [slug].html con navegacion cruzada
    Engine->>Disk: Actualiza index.html (Catalogo cronologico)
    Engine->>Disk: Actualiza latest.html (Puntero al mas reciente)
    Server-->>Edge: JSON {success, file_url, title, index_url}
    
    opt Si auto_open = true
        Server->>Usuario: Abre documento en el navegador predeterminado
    end
```

### Filosofia Zero-Bloatware

A diferencia de las arquitecturas empaquetadas basadas en Electron o frameworks web pesados, esta aplicacion no agrega ninguna capa de abstraccion innecesaria. No utiliza paquetes de terceros: no requiere `pip`, ni `flask`, ni `fastapi`, ni librerias de compilacion externas. Todo el servidor HTTP y el procesador de Markdown operan con modulos nativos del interprete de Python.

### Modo Aplicacion Chromium

La interfaz de usuario se despliega utilizando la instancia de Microsoft Edge (o Google Chrome) ya presente en el sistema operativo mediante el flag:

```cmd
msedge.exe --app="http://127.0.0.1:51870" --window-size=750,680 ...
```

Esto proporciona aceleracion completa por hardware, soporte para estilos CSS modernos (`backdrop-filter: blur`, variables CSS, grid/flexbox) y tipografia de ultra-alta definicion en una ventana independiente, limpia y sin distracciones de navegacion.

### Ciclo de Vida y Watchdog Defensivo

Para evitar que procesos de Python queden huerfanos en memoria:
- **Deteccion Nativa de Ventana (HWND Win32):** El servidor rastrea continuamente el identificador de ventana del navegador mediante `user32.IsWindow(hwnd)`. Mientras la ventana exista (incluso minimizada o en segundo plano), el servidor permanece activo.
- **Web Worker de Latidos Inmune a Throttling:** Un worker en segundo plano emite peticiones periodicas `POST /api/heartbeat` para evitar que las restricciones de suspension de Chromium detengan la aplicacion.
- **Apagado Limpio y Diferenciado:** Al cerrar la ventana desde la `X`, si el modo bandeja esta activo, el navegador libera los ~150 MB de Chromium pero mantiene el servidor en reposo; si el modo bandeja esta desactivado, programa el apagado ordenado tras 4 segundos de gracia.

### Integracion en el System Tray y Guardian de Instancia Unica

La aplicacion implementa soporte completo para la bandeja del sistema (area de notificacion de Windows junto al reloj) mediante el modulo nativo `tray_manager.py`:

- **Cero Dependencias Externas (Win32 ctypes):** Control directo mediante `Shell_NotifyIconW` en `shell32.dll` y `user32.dll` sobre un hilo daemon dedicado (`SystemTrayThread`).
- **Ahorro de Memoria y Reapertura Ultrarrapida (< 200 ms):** Al cerrar la ventana con la `X`, Microsoft Edge se cierra (liberando ~150 MB de memoria RAM), mientras `pythonw.exe` permanece en reposo en la bandeja consumiendo apenas ~14 a 18 MB de RAM y 0% de CPU. Al pulsar el icono con un clic o doble clic, la ventana se restaura o relanza de inmediato sin demoras de inicio frio.
- **Menu Contextual Nativo (Clic Derecho):** Incluye accesos directos a *📌 Abrir Markdown to HTML*, *📂 Abrir Carpeta de Documentos*, *📚 Ver Biblioteca (index.html)* y *❌ Salir completamente*.
- **Notificacion en Globo Informativa (Balloon Tip):** Al enviar la app a la bandeja por primera vez, muestra un globo informativo nativo de Windows confirmando que la app sigue disponible en segundo plano.
- **Guardian de Instancia Unica (*Single Instance Guard*):** Protegido mediante un Named Mutex de Windows (`Local\MarkdownToHTML_App_SingleInstance_Mutex`). Si el usuario vuelve a dar doble clic al acceso directo cuando la app ya esta en la bandeja, la nueva instancia despierta la app activa mediante `/api/open-app` y finaliza de inmediato, evitando procesos o iconos duplicados.

### Integracion Win32 para Portapapeles

Los navegadores basados en Chromium exigen confirmacion explicita del usuario cada vez que una pagina web intenta leer el portapapeles mediante la API web `navigator.clipboard.readText()`. 

Para erradicar este mensaje:
1. El frontend consulta el endpoint `/api/clipboard`.
2. El servidor en `app.py` utiliza la API Win32 de Windows (`OpenClipboard`, `GetClipboardData` con formato `CF_UNICODETEXT`, `GlobalLock` y `GlobalUnlock` de 64 bits mediante `ctypes`).
3. El contenido se lee en memoria en menos de 1 milisegundo y se retorna como JSON al frontend sin disparar alertas ni solicitar permisos adicionales.

### Cache Inteligente contra Bloqueo de Antivirus

Cuando se generan documentos que incluyen diagramas Mermaid, el archivo HTML almacena el script embebido de Mermaid (~2.8 MB) para mantener la portabilidad offline. Al escanear la biblioteca para regenerar `index.html`, Windows Defender o programas antivirus pueden ralentizar la lectura repetitiva de archivos pesados.

Para solventar esto:
- La aplicacion implementa una cache persistente de metadatos en `.index_cache.json`.
- Cada archivo se identifica por una clave compuesta `(filename, mtime, size_kb)`.
- Si el archivo no ha sufrido modificaciones en disco, su titulo y metadatos se recuperan desde la cache en memoria **sin abrir el archivo fisico**, logrando una regeneracion del indice instantanea (< 5 ms).

---

## Estructura del Proyecto

```text
MarkdownToHTML_App/
│
├── app.py                     # Servidor HTTP local, API REST y orquestador de ventana nativa
├── tray_manager.py            # Administrador nativo del System Tray de Windows (Win32 ctypes)
├── md_engine.py               # Motor de compilacion de Markdown a HTML (sin dependencias)
├── config.template.json       # Plantilla limpia de configuracion rastreada en Git
├── config.json                # Configuracion local persistente (aislada en .gitignore)
├── instalar.bat               # Instalador rapido de 1 clic para Windows (%LOCALAPPDATA%)
├── desinstalar.bat            # Desinstalador limpio de accesos directos y archivos
├── install_shortcuts.ps1      # Generador y eliminador de accesos directos de Windows
├── launch.vbs                 # Lanzador silencioso en VBScript (sin consola negra)
├── run.bat                    # Lanzador rapido por lotes
├── run_tests.py               # Ejecutor maestro de la suite integral de pruebas (126 tests)
├── verify_app.py              # Suite rapida de verificacion de humo (10 checks)
├── README.md                  # Manual tecnico y documentacion del proyecto
├── GIT_FLOW.md                # Estandar formal de ramas Git Flow y ciclo de ingenieria
│
├── tests/                     # Suite modular de pruebas con unittest nativo
│   ├── __init__.py            # Inicializador del paquete de pruebas
│   ├── test_helpers.py        # Entorno aislado en carpetas temporales y mocks
│   ├── test_md_engine.py      # 58 tests: AST, llamadas, tablas, kbd, listas, mermaid, cache
│   ├── test_app_api.py        # 23 tests: Endpoints REST, loopback real, tray, portapapeles, logs
│   ├── test_tray_manager.py   # 6 tests: Estructuras Win32, ciclo de vida del hilo, menus y globo
│   ├── test_window_geometry.py# 7 tests: Dimensionamiento responsivo de ventana
│   ├── test_config_and_history.py # 9 tests: Persistencia, limites y purga de fantasmas
│   ├── test_installer_and_distribution.py # 15 tests: Integridad de instalador y accesos directos
│   └── test_security.py       # 5 tests: Defensa contra Path Traversal, proteccion y XSS
│
├── ui/
│   └── index.html             # Interfaz grafica SPA (HTML5, CSS3, Vanilla JS sin frameworks)
│
└── assets/
    ├── app_icon.ico           # Icono nativo multirresolucion para Windows (256x256)
    ├── app_icon.png           # Isotipo oficial en alta resolucion
    ├── mermaid.min.js         # Runtime embebido offline de Mermaid (Mermaid 11.x)
    └── generate_icon.ps1      # Generador vectorial del icono mediante System.Drawing
```

---

## Pruebas Automatizadas y Calidad de Codigo

El proyecto cuenta con una suite integral de **126 pruebas automatizadas** que validan la funcionalidad del compilador, la API REST, la seguridad, la persistencia, la bandeja del sistema, la geometria de pantalla y la distribucion del instalador:

```powershell
# Ejecutar suite integral completa (126 tests con metricas detalladas):
python run_tests.py

# O ejecutar verificacion rapida de humo (10 checks):
python verify_app.py
```

### Cobertura de Pruebas

- **`tests/test_md_engine.py` (58 tests):** Analizador lexico y sintactico, bloques Mermaid interactivos y offline, tokens de diseno de tema claro/oscuro, alertas GitHub con SVG, tablas con alineacion, atajos `[[kbd:...]]`, jerarquia de listas anidadas, badges de estado, slugify y cache inteligente de metadatos.
- **`tests/test_app_api.py` (23 tests):** API REST del servidor HTTP sobre loopback real (`127.0.0.1`), codigos de estado HTTP, lectura nativa de portapapeles Win32, modo tray y endpoints `/api/open-app`, `/api/quit-app`, asignacion de puerto preferido y dinámico, servicio de assets estaticos, validacion de esquemas y logs.
- **`tests/test_tray_manager.py` (6 tests):** Validacion de estructuras ctypes Win32 de 64 bits (`NOTIFYICONDATAW`), ciclo de vida de arranque y detencion del hilo, despacho asincrono de callbacks, proteccion defensiva de globo y fallback ante ausencia de icono.
- **`tests/test_window_geometry.py` (7 tests):** Deteccion automatica de resolucion de pantalla (escritorio vs. laptop), dimensiones adaptativas y centrado nativo.
- **`tests/test_config_and_history.py` (9 tests):** Persistencia de configuracion, recuperacion ante JSON corrupto, limite estricto de 10 elementos en el historial y purga automatica de archivos eliminados.
- **`tests/test_installer_and_distribution.py` (15 tests):** Integridad sintactica de `instalar.bat` y `desinstalar.bat`, creacion y eliminacion de accesos directos `.lnk` y rutas con espacios.
- **`tests/test_security.py` (5 tests):** Prevencion de Path Traversal en `/assets/`, proteccion contra eliminacion de archivos del sistema e inmunidad de `index.html` y `latest.html`, y sanitizacion contra ataques XSS.

---

## Desinstalacion

Si en algun momento deseas remover la aplicacion del sistema:

1. Ejecuta **`desinstalar.bat`** (disponible en la carpeta de instalacion o en el repositorio clonado).
2. El script eliminara automaticamente:
   - Los accesos directos del **Escritorio** y del **Menu Inicio**.
   - Los archivos de la aplicacion en `%LOCALAPPDATA%\Programs\MarkdownToHTML_App`.
3. **Nota de Seguridad:** Tus documentos HTML compilados en tu carpeta de biblioteca **nunca seran eliminados**.

---

## Estandar de Contribucion y Git Flow

El desarrollo de este proyecto se rige estrictamente por el estandar **Git Flow** y la especificacion **Conventional Commits**:

- Consulta la guia completa de ciclo de vida en [GIT_FLOW.md](file:///c:/General/MarkdownToHTML_App/GIT_FLOW.md).
- **Ramas Principales:**
  - `master`: Codigo en produccion y versiones estables publicadas.
  - `develop`: Rama base para la integracion continua de caracteristicas.
- **Ramas de Trabajo:**
  - `feature/<nombre>`: Nuevas funcionalidades.
  - `bugfix/<nombre>`: Correcciones de errores.
  - `refactor/<nombre>`: Mejoras de arquitectura o rendimiento.
  - `docs/<nombre>`: Actualizaciones de documentacion o reglas.
  - `test/<nombre>`: Nuevas suites o casos de prueba.
- **Requisito de Integracion:** Toda contribucion debe contar con cobertura de pruebas y alcanzar el **100% de exito (0 fallos)** en `run_tests.py` antes de fusionarse.

---

## Licencia

Este proyecto se distribuye bajo la licencia **MIT**. Consulta el archivo `LICENSE` para mas detalles.
