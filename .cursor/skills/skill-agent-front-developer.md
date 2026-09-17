---
name: skill-agent-front-developer
description: >-
  Router for the front-developer agent. Opens skill-frontend-developer.
  Does not run /app-layer or tests in the same pass.
disable-model-invocation: true
owner: front-developer
---

# Скилл агента front-developer

Выполни `.cursor/skills/skill-frontend-developer.md` (команда `/frontend`).
Тесты в этом ходе не пиши и не гоняй. Рапорт — ПМ (конвейер) или пользователю только при прямом `/frontend` (сценарий S5: тогда можно предложить `/new-tests` / `/use-tests`).
Не открывай алгоритм `skill-app-layer`.
