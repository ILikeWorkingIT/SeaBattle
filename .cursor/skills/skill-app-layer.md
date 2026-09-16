---
name: skill-app-layer
description: >-
  Use when the user asks to implement the application/backend layer: FastAPI,
  Redis sessions, WebSocket, DDD layers, heatmap bot, or runs /app-layer.
  No PySide6 in domain/application/infrastructure. Do not use for UI chrome
  (/frontend), click-only mockups (/ui-prototyping), or running the suite
  (/use-tests).
disable-model-invocation: true
owner: back-developer
---

# Прикладной слой (API и домен за клиентом)

Скилл автономного application-инженера (ручной вызов **`/app-layer`**). Не подставляй факты другого проекта. Поведение — только из `Axxxx`, ФТ, UC, доменной модели, OpenAPI и явного запроса.

Стек: **Python 3.12+**, **FastAPI**, **Uvicorn**, **Redis**, REST + WebSocket. Канон слоёв: DDD / Clean Architecture.

Пока каталога `src/backend/` нет — **создавай его только в этом скилле по задаче реализации**, не «заодно» с правкой MAS-документов. Этот скилл не генерирует сервер сам при переносе методологии.

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

---

## 2. Редирект

| Запрос | Действие |
| --- | --- |
| Только макет | `/ui-prototyping` |
| Только виджеты / тема | `/frontend` |
| Только тесты / прогон | `/new-tests` / `/use-tests` |
| Только OpenAPI YAML | `/openai` |

Не выполняй `/use-tests` в этом ходе. Unit-тесты домена без GUI — можно добавить в `tests/` по SOP, полный прогон предложи отдельно.

---

## 3. Контракт

- Операции HTTP/WS — только те, что есть в `requirements/openapi.yaml` и связанных ФТ/UC. Не выдумывай endpoint.
- Вход/выход use case — типизированные модели (Pydantic / dataclass), не `dict[str, Any]`.
- Heatmap-бот — доменный сервис по ТЗ; не подменяй случайной стрельбой, если в источниках heatmap.

---

## 4. SOP (один режим)

| Режим | Когда |
| --- | --- |
| **фича** | служба / use case / endpoint по ФТ / UC / DDD / OpenAPI |
| **баг** | гонка сессии, TTL, WS, инвариант поля |

Режим **фича:** нет канона — спроси с рекомендацией.

Порядок: OpenAPI + ФТ → слой → Redis/порт → не трогать `src/frontend/` → не коммить.

---

## Запрещено

- Импорт PySide6 в domain/application/infrastructure.
- Gradio, Flask «вместо FastAPI», если канон — FastAPI.
- Смешивать с правкой GUI в одном ответе.
- Новая зависимость вне канона ТЗ без явной просьбы. По канону допустимы: FastAPI, Uvicorn, redis-клиент, pydantic-settings — когда реализуешь соответствующий кусок.
