---
name: skill-app-layer
description: >-
  Use when the user asks to implement the application/backend layer: FastAPI,
  Redis sessions, WebSocket, DDD layers, heatmap bot, Docker Compose scaffold,
  or runs /app-layer. No PySide6 in domain/application/infrastructure. Do not
  use for UI chrome (/frontend), click-only mockups (/ui-prototyping), or
  running the suite (/use-tests).
disable-model-invocation: true
owner: back-developer
---

# Прикладной слой (API и домен за клиентом)

Скилл автономного application-инженера (ручной вызов **`/app-layer`**). Не подставляй факты другого проекта. Поведение — только из `Axxxx`, ФТ, UC, доменной модели, OpenAPI и явного запроса.

Стек: **Python 3.12+**, **FastAPI**, **Uvicorn**, **Redis**, REST + WebSocket. Канон слоёв: DDD / Clean Architecture. Инфра по ТЗ §2.4: **Docker**, **Docker Compose**, **pydantic-settings**.

Пока каталога `src/backend/` нет — **создавай его только в этом скилле по задаче реализации**, не «заодно» с правкой MAS-документов. Этот скилл не генерирует сервер сам при переносе методологии.

Имя команды `/app-layer` = работа с бэкендом Sea Battle (`src/backend/`). Не переименовывай в `/backend` без явного запроса.

---

## 1. Роль и границы

Роль: **Senior Application Engineer**.

| Слой | Путь (план) | Знает | Не знает |
| --- | --- | --- | --- |
| Domain | `src/backend/domain/` | сущности, инварианты флота/выстрела | FastAPI, Redis, PySide6 |
| Application | `src/backend/application/` | use case, порты | виджеты |
| Infrastructure | `src/backend/infrastructure/` | Redis, адаптеры | Qt |
| Presentation | `src/backend/presentation/` | HTTP/WS handlers | правила UI-хрома |

В `domain/` и `application/` **запрещён** импорт `PySide6`, `fastapi`, `redis` (инфраструктурные SDK — только infrastructure/presentation).

Порт внешнего хранилища = Redis (сессии с TTL, счётчики). SQL не вводи без источника.

**Вне этого скилла (клиент):** UC-008 (смена языка) — локально на Фронтенде; сюда не тащи. Язык сессии на Бэкенде не хранить (A0091).

---

## 2. Редирект

| Запрос | Действие |
| --- | --- |
| Только макет | `/ui-prototyping` |
| Только виджеты / тема / UC-008 | `/frontend` |
| Только тесты / прогон | `/new-tests` / `/use-tests` |
| Только OpenAPI YAML | `/openai` |

Не выполняй `/use-tests` и `/new-tests` в этом ходе. Файлы в `tests/` **не** создавай и не правь: покрытие — скилл tester / команда `/new-tests`. В отчёте хода предложи `/new-tests` **только** при прямом вызове `/app-layer` (сценарий S5). Если ход от ПМ — рапорт ПМ, без slash пользователю.

---

## 3. Контракт

- Операции HTTP/WS — только те, что есть в `requirements/openapi.yaml` и связанных ФТ/UC. Не выдумывай endpoint.
- Вход/выход use case — типизированные модели (Pydantic / dataclass), не `dict[str, Any]`.
- Heatmap-бот — доменный сервис по ТЗ; не подменяй случайной стрельбой, если в источниках heatmap.
- Порт API по канону: `http://localhost:8000` (A0160). Preview OpenAPI на 8080/8081 — не путать с живым сервером.

---

## 4. SOP — выбор режима

Выбери **один** режим на ход:

| Режим | Когда |
| --- | --- |
| **каркас** | Нет `src/backend/` или нет Compose/манифеста; задача «поднять сервер», «scaffold», «скелет» |
| **фича** | Служба / use case / endpoint по ФТ / UC / DDD / OpenAPI |
| **баг** | Гонка сессии, TTL, WS, инвариант поля, Redis |

Нет канона или неясен срез — спроси с **рекомендацией** (обычно: сначала каркас, затем UC по очереди ниже).

Общий порядок любого режима: канон (`openapi.yaml` + ФТ/`Axxxx` + DDD) → код слоёв → Redis/порт → не трогать `src/frontend/` → не коммить без просьбы.

---

## 5. Режим «каркас» (MVP bootstrap)

Цель одного хода: пустой, но **запускаемый** скелет бэкенда + Redis через Compose. Не реализуй всю игру в том же ответе.

### 5.1. Каталоги и точки входа

Создай (если нет):

```
src/backend/
  domain/
  application/
  infrastructure/
  presentation/
  __init__.py          # пакет
  main.py              # FastAPI app + lifespan (подключение Redis)
src/backend/requirements.txt
.env.example           # только несекретные ключи (REDIS_URL, HOST, PORT)
docker-compose.yml     # сервисы: redis + backend (см. §5.2)
```

Пустые `__init__.py` в слоях допустимы. Минимальный health: например `GET /health` **только если** он уже в OpenAPI или пользователь явно просил; иначе достаточно успешного старта Uvicorn и ответа по существующему пути из контракта (после первой фичи — `GET /statistics` или `POST /sessions`).

### 5.2. Docker Compose (ТЗ §2.4)

- Сервисы минимум: **`redis`**, **`backend`** (образ/сборка из `src/backend`, Uvicorn на `8000`).
- Redis — внутренний хост для backend; с хоста наружу пробрасывать порт Redis только если нужно для отладки (по умолчанию можно не экспонировать).
- Backend зависит от healthy Redis; idle TTL сессий — ответственность приложения/ключей Redis (30 мин по `A0022`), не «магия» Compose.
- Не ставь GUI / PySide6 в образ backend.
- **Данные на хосте (тома / установки «в Docker»):** корень — `F:\Docker\<имя>` (пример: `F:\Docker\ollama`). В `docker-compose.yml` для bind mount указывай **прямой** путь в стиле Docker Desktop: `F:/Docker/ollama/` (или нужный подкаталог). Для Redis Sea Battle: `F:/Docker/redis/` → `/data`. Запрещено: `%CD%`, `%~dp0`, `$(pwd)`, относительные пути «от места запуска» и прочие DOS/shell-трюки для выяснения каталога. Источник: `reports/agent-memory.md` (2026-09-16).
- Запуск контейнеров — **только с разрешения пользователя** (см. MAS / `AGENTS.md`). В отчёте хода напиши команды `docker compose up`, но не поднимай Docker сам, пока пользователь не разрешил.

Локальный запуск без Docker (для разработки) тоже опиши в ответе: `uvicorn` + внешний Redis, если пользователь так предпочёл; канон инфраструктуры — Compose.

### 5.3. Зависимости каркаса

В `src/backend/requirements.txt` по канону ТЗ (без лишнего): FastAPI, Uvicorn, redis-клиент (async), pydantic-settings. Остальное — только по явной просьбе или когда фича реально требует.

### 5.4. После каркаса

Кратко: пути, как поднять Redis/API, что **ещё не** реализовано. Предложи следующий ход: **фича UC-001** (не весь бэклог сразу). `/frontend` и `/use-tests` в этом ходе не выполняй.

---

## 6. Режим «фича» — порядок по UC (MVP)

Один ход = **один** вертикальный срез (use case или явная группа из запроса). Не пытайся закрыть UC-001…007 за один ответ.

Рекомендуемый порядок (зависимости из `requirements/use-cases/list-uc.md`):

| Шаг | Срез | Что появляется на сервере | OpenAPI / канал |
| --- | --- | --- | --- |
| 0 | Каркас | §5 | Compose, app entry |
| 1 | **UC-001** | Создание PvE-сессии, генерация двух полей, лимит 3 сессии, отказ при сбое расстановки | `POST /sessions` |
| 2 | **UC-007** | Глобальная статистика (можно сразу после каркаса или после UC-001; независима от партии) | `GET /statistics` |
| 3 | **UC-002** + канал | Выстрел игрока; REST-выстрел — отказ | WS `/sessions/{id}/ws` + кадры shot; REST `…/shots` → 4xx по контракту |
| 4 | **UC-003** | Ход Бэкенда (heatmap), push состояния | те же WS-события |
| 5 | **UC-004** | `GAME_OVER`, атомарная статистика, освобождение слота | WS `GAME_OVER` + запись счётчиков |
| 6 | **UC-005** | Сдача по WS; REST-сдача — отказ | WS surrender; REST `…/surrender` → 4xx |
| 7 | **UC-006** | Возобновление по id, replace connection, TTL не сдвигать reconnect'ом | тот же WS upgrade |

**Не на бэкенде:** UC-008 → `/frontend`.

Если пользователь назвал конкретный UC / operationId — делай его, но предупреди, если нарушен порядок (например UC-002 без UC-001 и без WS-каркаса).

Внутри фичи: domain-инварианты → application use case + порты → Redis-адаптер → presentation (router/WS) → не трогать `src/frontend/` и `tests/`.

---

## 7. Режим «баг»

Минимальный дифф. Сначала воспроизведи по ФТ/`Axxxx`/OpenAPI (ожидаемый код, кадр, инвариант). Не раздувай рефакторингом соседних UC.

Типичные зоны: лимит сессий, idle TTL, гонка выстрел/сдача, replace WS, пустая heatmap / `SESSION_ABORTED`, идемпотентность событий.

---

## Запрещено

- Импорт PySide6 в domain/application/infrastructure.
- Gradio, Flask «вместо FastAPI», если канон — FastAPI.
- Смешивать с правкой GUI в одном ответе.
- Реализовывать UC-008 на сервере.
- Новая зависимость вне канона ТЗ без явной просьбы. По канону допустимы: FastAPI, Uvicorn, redis-клиент, pydantic-settings — когда реализуешь соответствующий кусок; Docker/Compose-файлы — в режиме каркас.
- Поднимать Docker / GUI из терминала агента без разрешения пользователя.
- Писать или править `tests/` (это `/new-tests`).
- Выдумывать endpoint вне `requirements/openapi.yaml`.
