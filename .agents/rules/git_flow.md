# Regla de Workspace: Protocolo de Flujo de Trabajo (Git Flow & Modos Operativos)

Todo agente que interactúe con este repositorio debe clasificar el requerimiento del usuario y actuar estrictamente bajo una de las dos modalidades definidas en [GIT_FLOW.md](file:///c:/General/MarkdownToHTML_App/GIT_FLOW.md):

---

## 1. MODO CONSULTIVO / PROPUESTA PREVIA (Si el usuario pregunta, consulta o pide evaluar)
*Gatilladores:* "¿Podríamos...?", "Analiza si...", "Quiero ver primero...", "Cómo se vería...", "Evalúa...".

**Comportamiento Obligatorio:**
- **PROHIBIDO:** Modificar código fuente, crear ramas de Git o realizar commits.
- **ACCIONES:**
  1. Inspeccionar la base de código sin alterarla.
  2. Redactar una propuesta técnica clara (arquitectura Zero-Bloatware, alternativas, maquetas/snippets de interfaz o API).
  3. Indicar el impacto esperado (archivos involucrados y pruebas a diseñar).
  4. Preguntar al usuario si desea proceder con la implementación mediante el Flujo Grande.

---

## 2. EL FLUJO GRANDE DE EJECUCIÓN (Si el usuario ordena hacer una mejora directamente o aprueba una propuesta)
*Gatilladores:* "Hazlo", "Implementa...", "Corrige...", "Agrega...", "Procede".

> [!CAUTION]
> ### REGLA DE ORO INVIOLABLE: NUNCA DESARROLLAR DIRECTAMENTE EN `develop` NI EN `master`
> Antes de escribir una sola línea de código, crear un archivo nuevo o modificar una prueba, el agente **DEBE OBLIGATORIAMENTE crear y posicionarse en la rama de trabajo correspondiente**. No se tolerará código huérfano ni commits directos en ramas principales.

### Ciclo de 8 Fases Obligatorio del Desarrollador Profesional:

1. **Fase 1: Planificar y Diseñar:**
   - Desglosar requisitos, contratos de interfaz y estrategia TDD.
   - Presentar o validar el plan técnico.

2. **Fase 2: Ramificar en Git Flow (ANTES DE CUALQUIER CAMBIO):**
   - Verificar estado limpio en `develop`: `git checkout develop`.
   - Crear rama de trabajo específica:
     - Nuevas características: `git checkout -b feature/<nombre-descriptivo>`
     - Corrección de errores: `git checkout -b bugfix/<nombre-descriptivo>`
     - Refactorizaciones: `git checkout -b refactor/<nombre-descriptivo>`
     - Mejoras de pruebas: `git checkout -b test/<nombre-descriptivo>`

3. **Fase 3: Desarrollo Cíclico e Incremental:**
   - Implementación limpia, modular y desacoplada.
   - Respetar estándar Zero-Bloatware (Python stdlib y Vanilla JS/CSS puro).

4. **Fase 4: Testing Exhaustivo (Quality Gate):**
   - Diseñar e implementar pruebas unitarias y de sistema en `tests/`.
   - Ejecutar suite integral: `python run_tests.py` (100% de éxito requerido, 0 fallos).

5. **Fase 5: Sincronización de Reglas y Contexto .md (OBLIGATORIO):**
   - Documentar de inmediato las nuevas reglas de negocio, endpoints, patrones o decisiones en:
     - `.agents/AGENTS.md`
     - `.agents/rules/*.md`
     - `README.md`
     - `GIT_FLOW.md`

6. **Fase 6: Commits Atómicos y Progresivos (Conventional Commits):**
   - **Prohibido realizar un único commit genérico con todo mezclado.**
   - Separar lógicamente los commits:
     - `feat(<scope>): ...` para código fuente nuevo o modificado.
     - `test(<scope>): ...` para pruebas unitarias e integración.
     - `docs(<scope>): ...` para documentación, manuales y reglas de contexto.
     - `refactor(<scope>): ...` para reestructuraciones sin cambio de funcionalidad.

7. **Fase 7: Merge Limpio con `--no-ff` y Limpieza de Ramas:**
   - Asegurar que la suite completa pase al 100% en la rama de trabajo.
   - Cambiar a `develop`: `git checkout develop`.
   - Integrar sin fast-forward: `git merge --no-ff feature/<nombre> -m "merge: feature/<nombre> into develop"`.
   - Re-ejecutar `python run_tests.py` sobre `develop` para certificar la integración.
   - Eliminar la rama local de trabajo: `git branch -d feature/<nombre>`.

8. **Fase 8: Cierre de Ticket, Resumen Estandarizado y Comandos Git:**
   - De acuerdo con [closing_protocol.md](file:///c:/General/MarkdownToHTML_App/.agents/rules/closing_protocol.md), cada tarea es un **Ticket**.
   - Proporcionar de forma obligatoria el **Resumen Estandarizado de Cierre de Ticket** (Cambios realizados, Cosas nuevas, Pruebas existentes, Pruebas nuevas, Archivos modificados y Creados).
   - Presentar la **Retrospectiva de Auto-mejora**: si no hay mejoras al contexto mencionarlo explícitamente; si se identificó una mejora, indicar archivo, cambios propuestos y formular una pregunta de confirmación esperando un "SÍ" explícito del usuario antes de aplicar cambios en archivos de contexto.
   - Entregar el bloque completo de **Comandos Estandarizados de Git** (commits semánticos atómicos, merge `--no-ff` a `develop` y verificación de árbol limpio).
   - Mostrar el árbol de commits (`git log -n 5 --graph --oneline`) y `git status` limpio.
