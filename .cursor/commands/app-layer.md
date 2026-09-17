---
description: >-
  Прикладной слой и HTTP/WS API (FastAPI, Redis, DDD) по skill-app-layer.
  UI-хром — /frontend.
---

# Прикладной слой приложения

Прочитай и выполни `.cursor/skills/skill-app-layer.md` целиком. Команда `/app-layer` запускает этот скилл.

Это **слой за клиентом**: домен, use case, Redis, FastAPI, WebSocket. Каталог `src/backend/` (`domain/`, `application/`, `infrastructure/`, `presentation/`). В domain/application **запрещён** импорт PySide6. Это **не** вёрстка окна.

Не клади домен игры в `src/frontend/`. Клиентский HTTP — `/frontend`.

Не выполняй `.cursor/skills/skill-new-tests.md` и `.cursor/skills/skill-use-tests.md` в этом запуске. В `tests/` ничего не пиши. Полный прогон — отдельная `/use-tests` (её предлагает tester или пользователь в сценарии S5).

## Режим

По запросу выбери **один** (детали и порядок UC — в скилле §4–7):

- **каркас** — нет `src/backend/` / Compose: скелет DDD, `requirements.txt`, `.env.example`, `docker-compose.yml` (redis + backend :8000); без полной игры в том же ходе;
- **фича** — один вертикальный срез по UC / OpenAPI / `Axxxx` (рекомендуемый порядок: UC-001 → UC-007 → UC-002+WS → UC-003 → UC-004 → UC-005 → UC-006; UC-008 — не сюда);
- **баг** — сессия Redis, WS, TTL, инвариант поля, гонка.

`$1` и дальнейший текст — «каркас», какой UC / путь API, какие ID, баг.

Если просят только макет — **остановись**. Нужна `/ui-prototyping`. Только виджеты / UC-008 — `/frontend`. Только OpenAPI YAML без кода — `/openai`.

Docker Compose не поднимай без разрешения пользователя; команды запуска укажи в отчёте.

## После выполнения

Кратко: режим; какие модули / Compose-файлы; контракт (команда / DTO / исключения); что покрыть тестами (пути), без записи в `tests/`. Прямой вызов: предложи `/new-tests` / `/use-tests` / `/frontend`, не выполняй. Ход от ПМ: только рапорт ПМ.
