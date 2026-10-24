# Manual de Flujo de Trabajo Git Flow y Estándares de Ingeniería

Este documento establece el protocolo oficial de **Git Flow**, convenciones de commits y ciclo de vida de desarrollo para el proyecto **Markdown to HTML Desktop App**. Tanto agentes autónomos como desarrolladores humanos deben seguir estrictamente este flujo para garantizar estabilidad, trazabilidad y cero regresiones.

---

## 1. Principios Fundamentales

1. **Aislamiento Total de Cambios:** Ningún cambio de código o refactorización se realiza directamente sobre `master` o `develop`. Todo cambio nace en una rama de trabajo dedicada.
2. **Estabilidad Absoluta en `develop`:** La rama `develop` debe estar en estado compilable, funcional y con el 100% de la suite de pruebas (`run_tests.py` y `verify_app.py`) en verde en todo momento.
3. **Producción Intocable en `master`:** `master` refleja exclusivamente versiones estables en producción, etiquetadas con Tags de Versionado Semántico (SemVer: `vMAJOR.MINOR.PATCH`).
4. **Commits Semánticos Atómicos:** Cada commit debe representar una unidad lógica e indivisible de cambio siguiendo la especificación *Conventional Commits*.
5. **Zero-Bloatware:** Prohibido incorporar dependencias externas pesadas o no autorizadas (`node_modules`, paquetes no estándar en `pip`).
6. **Mejora Continua:** Este documento es un contexto vivo. Si se detecta una nueva necesidad, caso de borde o mejora de proceso, el protocolo se actualiza eVersiona.

---

## 2. Mapa y Taxonomía de Ramas

```mermaid
gitGraph
   commit id: "v1.0.0 (Init)" tag: "v1.0.0"
   branch develop
   checkout develop
   commit id: "develop base"
   branch feature/recent-history
   checkout feature/recent-history
   commit id: "feat: detect existing html files"
   commit id: "test: add history reload tests"
   checkout develop
   merge feature/recent-history id: "merge: feature/recent-history"
   branch release/v1.1.0
   checkout release/v1.1.0
   commit id: "chore: bump version v1.1.0"
   checkout master
   merge release/v1.1.0 id: "merge: release/v1.1.0" tag: "v1.1.0"
   checkout develop
   merge release/v1.1.0 id: "merge: sync back release"
```

### 2.1. Ramas Principales (Infinitas)

| Rama | Propósito | Reglas de Protección |
| :--- | :--- | :--- |
| **`master`** | Código listo para despliegue / distribución al usuario final. | Sólo recibe merges desde ramas `release/*` o `hotfix/*`. Cada merge genera un Tag SemVer (`vX.Y.Z`). |
| **`develop`** | Rama principal de integración continua y desarrollo activo. | Recibe merges de `feature/*`, `bugfix/*`, `release/*` y `hotfix/*`. Debe mantener el 100% de tests en verde. |

### 2.2. Ramas de Soporte (Temporales)

| Prefijo de Rama | Origen (Branch From) | Destino (Merge To) | Convención de Nombres | Ejemplo |
| :--- | :--- | :--- | :--- | :--- |
| **`feature/`** | `develop` | `develop` | `feature/<kebab-case-descriptivo>` | `feature/auto-reload-history` |
| **`bugfix/`** | `develop` | `develop` | `bugfix/<kebab-case-descriptivo>` | `bugfix/fix-window-restore-edge` |
| **`release/`** | `develop` | `master` y `develop` | `release/v<MAJOR>.<MINOR>.<PATCH>` | `release/v1.1.0` |
| **`hotfix/`** | `master` | `master` y `develop` | `hotfix/v<MAJOR>.<MINOR>.<PATCH>` | `hotfix/v1.0.1` |
| **`test/`** | `develop` | `develop` | `test/<kebab-case-descriptivo>` | `test/modular-test-suite` |

---

## 3. Especificación de Conventional Commits

Los mensajes de commit deben seguir estrictamente el siguiente formato:

```
<tipo>(<alcance opcional>): <descripción concisa en imperativo y minúsculas>

[cuerpo explicativo opcional: detalles del qué, el por qué y consideraciones]

[referencias opcionales: Closes #123, Fixes #45]
```

### 3.1. Tipos Permitidos

- **`feat`**: Nueva funcionalidad para el usuario o el motor (ej. `feat(server): auto-recargar documentos preexistentes en historial`).
- **`fix`**: Corrección de un defecto o error de lógica (ej. `fix(engine): corregir alineación de tablas markdown con celdas vacías`).
- **`docs`**: Cambios exclusivos en documentación (`README.md`, `AGENTS.md`, `GIT_FLOW.md`).
- **`style`**: Ajustes estéticos de CSS/UI o formato de código sin alterar lógica.
- **`refactor`**: Reestructuración de código sin agregar funcionalidad ni corregir bugs.
- **`perf`**: Optimizaciones de rendimiento de compilación o respuesta de API.
- **`test`**: Creación o refactorización de pruebas unitarias o de integración.
- **`chore`**: Tareas de mantenimiento, actualización de scripts de instalación o `.gitignore`.
- **`merge`**: Registro explícito de integración de ramas (`merge: feature/xyz into develop`).

### 3.2. Alcances Comunes en el Proyecto (`scope`)

- `(engine)`: Motor de compilación `md_engine.py`.
- `(server)`: Servidor HTTP y API local `app.py`.
- `(ui)`: Interfaz gráfica SPA `ui/index.html`.
- `(tests)`: Suite de pruebas `tests/` o runners.
- `(shortcuts)`: Scripts de acceso directo y empaquetado nativo Windows.

---

## 4. Protocolo Operativo Paso a Paso para Agentes y Desarrolladores

Cada requerimiento debe ejecutarse siguiendo este ciclo riguroso de 7 pasos:

```
[1. Inspeccionar & Sincronizar]
            ↓
  [2. Crear Rama Feature/Bugfix]
            ↓
  [3. Implementación & Pruebas TDD]
            ↓
  [4. Validación Integral (100% Pass)]
            ↓
  [5. Commits Atómicos Semánticos]
            ↓
  [6. Integración (Merge --no-ff a develop)]
            ↓
  [7. Limpieza & Documentación]
```

### Paso 1: Inspección y Sincronización Inicial
Antes de escribir cualquier línea de código:
```powershell
# 1. Comprobar estado limpio del directorio de trabajo
git status

# 2. Situarse en develop
git checkout develop

# 3. Verificar que no haya commits pendientes
git log -n 3 --oneline
```

### Paso 2: Creación de la Rama de Trabajo
```powershell
# Para una nueva característica:
git checkout -b feature/nombre-de-la-funcionalidad

# O para una corrección de bug:
git checkout -b bugfix/nombre-del-bug
```

### Paso 3: Implementación y Pruebas
1. Escribir código limpio respetando la arquitectura Zero-Bloatware de Python nativo.
2. Añadir o actualizar las pruebas unitarias correspondientes en `tests/`.
3. Nunca añadir al stage archivos de depuración como `debug_log.txt`, carpetas temporales `tmp/` o caches `__pycache__`.

### Paso 4: Validación y Control de Calidad Obligatorio
Antes de hacer commit, **TODAS las suites de pruebas deben ejecutarse y reportar 100% de éxito**:
```powershell
# Ejecutar suite exhaustiva modular (79+ pruebas)
python run_tests.py

# Ejecutar suite de pruebas de humo y ciclo de vida (9 checks)
python verify_app.py
```
> [!IMPORTANT]
> Si una sola prueba falla, queda terminantemente prohibido hacer commit o merge. Se debe depurar y corregir hasta alcanzar el 100% de éxito.

### Paso 5: Commits Atómicos
Añadir únicamente los archivos involucrados en el cambio:
```powershell
git add app.py ui/index.html tests/test_config_and_history.py
git commit -m "feat(server): auto-recargar historial con documentos existentes al abrir app"
```

### Paso 6: Integración Segura a `develop`
```powershell
# 1. Volver a la rama de integración
git checkout develop

# 2. Mergear preservando el historial completo mediante --no-ff
git merge --no-ff feature/nombre-de-la-funcionalidad -m "merge: feature/nombre-de-la-funcionalidad into develop"

# 3. Validar nuevamente la suite de pruebas sobre develop integrado
python run_tests.py
```

### Paso 7: Limpieza de la Rama de Trabajo
```powershell
# Eliminar la rama local una vez integrada exitosamente
git branch -d feature/nombre-de-la-funcionalidad
```

---

## 5. Procedimiento de Publicación de Release (`release/*`)

Cuando se acumula un conjunto significativo de funcionalidades en `develop` y se desea congelar una versión:

1. Crear rama `release/vX.Y.Z` a partir de `develop`:
   ```powershell
   git checkout develop
   git checkout -b release/v1.1.0
   ```
2. Realizar ajustes menores (actualizar versiones en `README.md`, `AGENTS.md` y notas de versión).
3. Ejecutar suite completa `python run_tests.py`.
4. Mergear a `master` y colocar Tag de versión:
   ```powershell
   git checkout master
   git merge --no-ff release/v1.1.0 -m "merge: release/v1.1.0 into master"
   git tag -a v1.1.0 -m "Release v1.1.0: Auto-recarga de historial y catálogo interactivo"
   ```
5. Mergear los cambios de release de vuelta a `develop`:
   ```powershell
   git checkout develop
   git merge --no-ff release/v1.1.0 -m "merge: sync back release/v1.1.0 into develop"
   ```
6. Eliminar la rama `release/v1.1.0`:
   ```powershell
   git branch -d release/v1.1.0
   ```

---

## 6. Procedimiento para Hotfixes Críticos en Producción (`hotfix/*`)

Si se detecta un fallo crítico en la versión de producción (`master`):

1. Crear la rama de hotfix desde `master`:
   ```powershell
   git checkout master
   git checkout -b hotfix/v1.0.1
   ```
2. Aplicar la corrección mínima y verificar con `run_tests.py`.
3. Mergear a `master`, etiquetar y propagar inmediatamente a `develop`:
   ```powershell
   git checkout master
   git merge --no-ff hotfix/v1.0.1 -m "merge: hotfix/v1.0.1 into master"
   git tag -a v1.0.1 -m "Hotfix v1.0.1: Parche urgente de seguridad"

   git checkout develop
   git merge --no-ff hotfix/v1.0.1 -m "merge: propagate hotfix/v1.0.1 into develop"

   git branch -d hotfix/v1.0.1
   ```

---

## 7. Reglas de Protección y Buenas Prácticas

- **Nunca usar `git push --force`** ni reescribir la historia pública de commits compartidos.
- **Mantener `.gitignore` al día:** Garantizar que `config.json` local (si contiene rutas privadas), `debug_log.txt`, `.tmp` y `__pycache__` no se comiteen accidentalmente si no corresponden al baseline.
- **Trazabilidad en Mensajes de Merge:** Los merges siempre deben usar `--no-ff` y un mensaje estándar descriptivo: `"merge: <rama-origen> into <rama-destino>"`.
- **Evolución del Protocolo:** Si se identifica un nuevo escenario o regla de ingeniería, este documento debe actualizarse mediante una rama `docs/improve-git-flow` o en la rama de trabajo correspondiente.
