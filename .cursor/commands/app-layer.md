---
description: >-
  Прикладной слой и HTTP/WS API (FastAPI, Redis, DDD) по skill-app-layer.
  UI-хром — /frontend.
---

# Прикладной слой приложения

Прочитай и выполни `.cursor/skills/skill-app-layer.md` целиком. Команда `/app-layer` запускает этот скилл.

Это **слой за клиентом**: домен, use case, Redis, FastAPI, WebSocket. Каталог `src/backend/` (`domain/`, `application/`, `infrastructure/`, `presentation/`). В domain/application **запрещён** импорт PySide6. Это **не** вёрстка окна.

Не клади домен игры в `src/frontend/`. Клиентский HTTP — `/frontend`.

Не выполняй `.cursor/skills/skill-new-tests.md` и `.cursor/skills/skill-use-tests.md` в этом запуске. Unit-тесты без GUI — по SOP скилла. Полный прогон предложи `/use-tests` отдельно.

## Режим

По запросу выбери **один**:

- **фича** — служба / endpoint / use case по ФТ / UC / DDD / OpenAPI / `Axxxx`;
- **баг** — сессия Redis, WS, инвариант поля, гонка.

`$1` и дальнейший текст — какой use case или путь API; какие ID; баг.

Если просят только макет — **остановись**. Нужна `/ui-prototyping`. Только виджеты — `/frontend`. Только OpenAPI YAML без кода — `/openai`.

## После выполнения

Кратко: режим; какие модули в `src/backend/`; контракт (команда / DTO / исключения); какие pytest без GUI добавлены; предложи `/use-tests` и при нужде `/frontend`. В этом запуске их не выполняй.
