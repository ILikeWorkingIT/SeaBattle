# Архитектура MVP (as-is)

Источники: `src/backend/`, `src/frontend/`, `docker-compose.yml`, `requirements/openapi.yaml`. Диаграммы: [diagrams/diagram-c4-001.md](../../diagrams/diagram-c4-001.md).

На экране игроку сторона соперника подписана «Компьютер»; в этом файле канон документов — **Бэкенд**.

## Контейнеры

| Контейнер | Где | Порт |
| --- | --- | --- |
| Desktop UI | процесс на хосте, `python -m frontend` / `src/run-frontend.bat` | клиент к `:8000` |
| API | сервис Compose `backend`, FastAPI/Uvicorn | **8000** |
| Redis | сервис Compose `redis:7-alpine` | 6379 внутри сети Compose |

Клиент в Docker не входит. Просмотрщики OpenAPI на 8080/8081 — не runtime продукта.

## Слои бэкенда

```
presentation  sessions.py, statistics.py, ws.py, party_hub.py, schemas.py
application   StartSession, ApplyPlayerShot, PlayBackendTurns, ApplySurrender,
              CommitGameOver, GetStatistics; порты SessionRepository / LedgerRepository
domain        session, shot, heatmap, placement, surrender, ledger, types
infrastructure redis_session_store, redis_ledger_store, session_codec, settings
```

Точка входа: `src/backend/main.py` (`create_app`). Domain и application не импортируют PySide6.

## Слои фронтенда

| Пакет | Роль |
| --- | --- |
| `ui/` | лобби, бой, поле, флот, диалоги, статистика |
| `client/` | HTTP старт/статистика; `PartyChannelWorker` (WebSocket на GUI-потоке) |
| `settings_store.py`, `i18n.py` | язык RU/EN, QSettings; на API язык не уходит |
| `mock/` | статичная сцена разработки; живой старт партии — HTTP, не mock |

Правила боя на клиенте не считаются: UI отражает кадры и REST-снимки.

## Протокол

| Канал | Операции |
| --- | --- |
| `POST /sessions` | создать партию, в ответе флот **игрока**, без флота Бэкенда |
| `GET /statistics` | глобальные счётчики; партию и TTL не меняет |
| `GET /sessions/{id}/ws` | снимок, `shot`, `surrender`, `shotResolved`, `gameOver`, `sessionAborted`, `ttlExpired` |
| `POST …/shots`, `POST …/surrender` | отказ по контракту (не канал партии) |

## Redis (не SQL)

| Ключ | Тип | Смысл |
| --- | --- | --- |
| `seabattle:registry:slots` | SET | id активных сессий, лимит 3 |
| `seabattle:session:{id}` | STRING JSON + EX | состояние партии; EX = остаток idle |
| `seabattle:ledger:counters` | HASH | games, playerWins, backendWins, shotsSum |
| `seabattle:ledger:records` | LIST | записи завершённых партий |
| `seabattle:ledger:sessions` | SET | уже учтённые sessionId (идемпотентность A0129) |

Захват слота и запись исхода — Lua-скрипты в store. Heatmap в Redis **не** пишется.

## Что клиент не видит

- матрица вероятностей и режимы Hunt/Target;
- целые палубы флота Бэкенда до `SUNK`;
- чужой флот в `POST /sessions` (`backendFleet` в API не отдаётся).

## Связанные ADR

[adr-001](adr/adr-001-redis-not-sql.md) … [adr-005](adr/adr-005-heatmap-not-on-client.md).
