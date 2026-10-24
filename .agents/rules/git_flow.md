# Regla de Workspace: Flujo de Trabajo Git Flow

Sigue rigurosamente el manual de Git Flow definido en [GIT_FLOW.md](file:///c:/General/MarkdownToHTML_App/GIT_FLOW.md) para cualquier desarrollo, corrección de bugs, refactorización o adición de pruebas:

1. **Ramas Principales:**
   - `master`: Código estable de producción, con tags semánticos (`vX.Y.Z`).
   - `develop`: Integración continua. Todo cambio nace y regresa aquí a través de ramas dedicadas.
2. **Convención de Ramas:**
   - `feature/<kebab-case>`: Nuevas funcionalidades.
   - `bugfix/<kebab-case>`: Correcciones en desarrollo.
   - `release/v<SemVer>`: Preparación de versiones.
   - `hotfix/v<SemVer>`: Parches críticos en master.
   - `test/<kebab-case>`: Suites de pruebas.
3. **Conventional Commits Obligatorio:**
   - `<tipo>(<alcance>): <descripción>`
   - Tipos: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `merge`.
4. **Ciclo de Desarrollo Obligatorio (7 Pasos):**
   - 1. Verificar estado limpio en `develop`.
   - 2. Crear rama `feature/...` o `bugfix/...`.
   - 3. Implementar código limpio y pruebas unitarias (Zero-Bloatware).
   - 4. Ejecutar validación completa (`python run_tests.py` y `python verify_app.py`) - **100% de éxito obligatorio**.
   - 5. Commits atómicos con Conventional Commits.
   - 6. Merge hacia `develop` usando `git merge --no-ff <rama> -m "merge: <rama> into develop"`.
   - 7. Eliminar la rama local integrada (`git branch -d <rama>`).
