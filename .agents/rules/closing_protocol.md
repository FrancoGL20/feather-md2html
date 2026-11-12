# Regla de Workspace: Protocolo de Cierre, Limpieza y Auto-mejora Continua

Esta regla es de cumplimiento **obligatorio** para todo agente al finalizar una tarea, feature, corrección o proceso de desarrollo en este repositorio.

---

> [!IMPORTANT]
> **ENTREGA INMEDIATA Y OBLIGATORIA DEL FLUJO COMPLETO DE GIT EN EL MENSAJE DE IMPLEMENTACIÓN:**
> Siempre que el agente termine de implementar, corregir o refactorizar cualquier funcionalidad (Fases 3 y 4 concluidas con tests en verde), **DEBE INCLUIR OBLIGATORIAMENTE Y SIN EXCEPCIÓN** al final de esa misma respuesta la secuencia completa de comandos Git lista para copiar y ejecutar en un solo bloque, junto con el Resumen Estandarizado de Cierre de Ticket.
>
> **Principio de Revisión Previa por el Usuario:**
> El agente debe entregar esta secuencia teniendo plena consciencia del flujo humano:
> 1. El usuario **primero probará y revisará la funcionalidad** en su entorno real.
> 2. **Si todo funciona y está correcto**, el usuario procederá a copiar y ejecutar el bloque completo de comandos Git para cerrar el ciclo formalmente (commits, merge `--no-ff`, push a `origin develop` y poda de rama).
> 3. **Si surgen fallos, detalles visuales o ajustes requeridos**, el usuario **NO** ejecutará los comandos y le reportará los problemas al agente para iterar y corregir en la misma rama.
>
> **Antipatrón Estrictamente Prohibido (No dejar tickets huérfanos sin comandos):**
> Queda terminantemente prohibido que el agente termine una implementación y se limite a decir *"ya lo implementé, pruébalo"* omitiendo los comandos de cierre. El usuario nunca debe verse obligado a abrir un turno posterior para preguntar *«¿en qué paso estamos? ¿qué hay sin commit? dame su commit»*. Toda respuesta que concluya una implementación debe llevar sus comandos de cierre listos.
>
> La secuencia de comandos debe incluir:
> 1. Creación o posicionamiento en la rama de trabajo (`git checkout -b bugfix/<nombre>` o `feature/<nombre>` o `docs/<nombre>`).
> 2. `git add` y `git commit -m "..."` semánticos y atómicos.
> 3. Retorno exclusivo a develop (`git checkout develop`). Solo releases o hotfixes oficiales tocan `master`.
> 4. Merge sin fast-forward: `git merge --no-ff <rama> -m "merge: ..."`
> 5. Publicación en el repositorio remoto: `git push origin develop`.
> 6. Cierre y eliminación limpia de la rama local: `git branch -d <rama>`.
> 7. Comprobación final de árbol limpio (`git status` y `git log -n 5 --graph --oneline`).

## 1. Política Estricta de Archivos Temporales (`tmp/`)

1. **Ubicación Exclusiva:** Cualquier archivo efímero, vista previa HTML interactiva, mockups A/B, volcados de depuración o scripts de prueba rápidos **DEBEN crearse exclusivamente dentro del directorio `tmp/`** en la raíz del proyecto.
2. **Prohibición en Rutas de Producción:** Queda terminantemente prohibido generar archivos temporales en `ui/`, `assets/`, `tests/` o directamente en la raíz del repositorio.
3. **Ignorado en Git:** El directorio `tmp/` está registrado en `.gitignore` para garantizar que prototipos y archivos de prueba nunca contaminen el historial de commits.

---

## 2. Aislamiento de Runtime y Datos Locales (`config.json`)

1. **Datos de Sesión Excluidos de Git:** El archivo `config.json` almacena rutas absolutas del desarrollador y su historial reciente de conversiones. Está permanentemente ignorado en `.gitignore`.
2. **Plantilla Limpia (`config.template.json`):** Toda configuración estructural o nuevos parámetros deben definirse en `config.template.json` con valores neutros (`root_dir: ""`, etc.).
3. **Comportamiento del Backend:** `app.py` inicializa automáticamente `config.json` copiando desde `config.template.json` si no existe en el sistema anfitrión.

---

## 3. Protocolo de Cierre de Ticket (Los 5 Pasos Obligatorios)

> [!IMPORTANT]
> **Modelo de Trabajo por Tickets:** A partir de ahora, **toda nueva tarea, requerimiento, corrección o mejora solicitada por el usuario es tratada formalmente como un Ticket**. Todo ticket debe concluir obligatoriamente con el **Resumen Estandarizado de Cierre** y los **Comandos Git Estandarizados**.

Al terminar cualquier ticket o antes de dar por cerrada una sesión:

```mermaid
graph TD
    A[1. Purga y Limpieza] --> B[2. Aislamiento de Config/Runtime]
    B --> C[3. Ejecución de Tests Exhaustivos]
    C --> D[4. Revisión de Diff y Commits Semánticos]
    D --> E[5. Resumen Estandarizado y Comandos Git]
    E --> F[6. Retrospectiva de Auto-mejora]
```

1. **Paso 1: Purga y Limpieza de Basura:**
   - Verificar `git status`.
   - Limpiar o mover a `tmp/` cualquier archivo residual.
2. **Paso 2: Aislamiento de Configuración:**
   - Confirmar que ningún archivo local (como `config.json`) esté staged para commit.
3. **Paso 3: Validación Doble (Quality Gates):**
   - Ejecutar suite rápida: `python verify_app.py` (10/10 checks).
   - Ejecutar suite integral: `python run_tests.py` (100% éxito en todos los tests).
   - 100% de éxito requerido antes de hacer commit.
4. **Paso 4: Revisión de Diff y Commits Semánticos:**
   - Inspeccionar `git diff` y `git status`.
   - Estructurar commits con formato Conventional Commits (`feat:`, `test:`, `docs:`, `fix:`, `chore:`).
5. **Paso 5: Entrega Inmediata Obligatoria (Resumen Estandarizado de Cierre de Ticket y Comandos Git):**
   En la **misma respuesta** donde se entrega la solución implementada o corregida, el agente **DEBE SIEMPRE** proporcionar un resumen estandarizado y el bloque completo de comandos Git listo para ejecutar, con la siguiente estructura fija:
   - **📋 Resumen de Cambios:** Explicación técnica clara y concisa de las modificaciones realizadas.
   - **✨ Cosas Nuevas Incorporadas:** Nuevos módulos, dependencias offline, sintaxis soportadas o características añadidas.
   - **🧪 Pruebas Existentes Ejecutadas:** Total de pruebas previas verificadas con 100% de éxito (0 regresiones).
   - **🔬 Pruebas Nuevas Añadidas:** Detalle exhaustivo de las nuevas pruebas unitarias/integración creadas para el ticket.
   - **📂 Archivos Modificados y Creados:** Lista de archivos con etiquetas `[NEW]`, `[MODIFY]`, `[DELETE]`.
   - **💻 Comandos Estandarizados de Git:** Bloque de comandos listo para copiar/ejecutar en un solo clic con:
     1. Creación/cambio a rama de feature/bugfix/docs (`git checkout -b <tipo>/<nombre>`).
     2. `git add` y `git commit` semánticos atómicos (`feat:`, `test:`, `docs:`, etc.).
     3. Retorno exclusivo a la rama de integración (`git checkout develop`).
     4. Fusión formal preservando la historia (`git merge --no-ff <tipo>/<nombre> -m "merge: ..."`).
     5. Publicación remota (`git push origin develop`).
     6. Limpieza final de la rama local (`git branch -d <tipo>/<nombre>`).
     7. Verificación de árbol y status (`git status` y `git log -n 5 --graph --oneline`).
   
   > [!NOTE]
   > **Flujo de Ejecución del Usuario:** El agente entrega este bloque sabiendo que el usuario primero probará la funcionalidad. Si la prueba es satisfactoria, el usuario copiará y ejecutará el bloque en su consola para cerrar el ticket. Si detecta errores o ajustes pendientes, el usuario no ejecutará el bloque y le solicitará las correcciones al agente. Queda prohibido esperar a que el usuario pida los comandos para entregarlos.
6. **Paso 6: Retrospectiva y Propuesta de Auto-mejora Continua:**
   - **Caso 1: No se identificaron mejoras al contexto:**
     Mencionarlo explícitamente en el resumen final: `🎯 Retrospectiva de Auto-mejora: No se identificaron mejoras para agregar al contexto en este ticket.`
   - **Caso 2: Se identificó una mejora o patrón aplicable al contexto:**
     Aparece únicamente si durante la conversación se descubrió un patrón arquitectónico, solución a bug sutil, lección aprendida o regla a estandarizar que deba persistirse en el contexto (`.agents/AGENTS.md`, `.agents/rules/`, `README.md`, etc.).
     - **Archivo a modificar:** Mencionar la ruta exacta del archivo a actualizar.
     - **Contenido del cambio:** Explicar detalladamente qué sección y qué texto o directriz técnica se modificará o agregará.
     - **Pregunta de confirmación obligatoria:** Formularlo estrictamente como una pregunta. **PROHIBIDO aplicar el cambio de contexto automáticamente.** Solo si el usuario responde con un **"SÍ" explícito**, el agente procederá a aplicar el cambio en el archivo de contexto/regla.
