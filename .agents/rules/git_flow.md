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

**Ciclo de 7 Fases Obligatorio:**
1. **Fase 1: Planificar:** Desglosar requisitos, contratos de interfaz y estrategia TDD.
2. **Fase 2: Ramificar (Git Flow):**
   - Asegurar árbol limpio en `develop`: `git checkout develop`.
   - Crear rama de trabajo: `git checkout -b feature/<nombre>` o `bugfix/<nombre>`.
3. **Fase 3: Desarrollo Cíclico e Incremental:**
   - Implementación limpia y modular.
   - Respetar estándar Zero-Bloatware (Python stdlib y Vanilla JS/CSS puro).
4. **Fase 4: Testing Exhaustivo (Quality Gate):**
   - Implementar pruebas unitarias/integración en `tests/`.
   - Ejecutar `python run_tests.py` y `python verify_app.py`.
   - **Requisito Innegociable:** 100% de pruebas pasadas (79+ tests en verde). Cero fallos permitidos.
5. **Fase 5: Sincronización de Reglas y Contexto .md (OBLIGATORIO):**
   - Si hubo nuevas reglas de negocio, endpoints, patrones o decisiones arquitectónicas:
   - **Plasmarlas de inmediato** en los archivos de contexto:
     - `.agents/AGENTS.md`
     - `.agents/rules/*.md`
     - `README.md`
     - `GIT_FLOW.md` (si el proceso mejoró).
6. **Fase 6: Commits Atómicos y Merge a `develop`:**
   - Staging selectivo de archivos.
   - Conventional Commits: `<tipo>(<alcance>): <descripción>` (`feat`, `fix`, etc.).
   - Integrar a `develop`: `git checkout develop && git merge --no-ff <rama> -m "merge: <rama> into develop"`.
   - Revalidar suite de pruebas en `develop`.
   - Limpieza de rama integrada: `git branch -d <rama>`.
7. **Fase 7: Cierre y Demostración Ejecutiva:**
   - Reporte conciso con enlaces de archivo (`file:///`), resultados de pruebas y guía de validación.
