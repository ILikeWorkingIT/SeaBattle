# Конфигурация проекта

Заполнено по фактам репозитория (не копия чужого продукта). Источники: `documentation/specification-sea-battle-v1-1.md`, `README.md`, `requirements/openapi.yaml`.

## Продукт

| Поле | Значение |
| --- | --- |
| Имя | Sea Battle |
| Тип | Desktop PvE, клиент–сервер |
| Назначение | Пошаговый «Морской бой»: игрок против серверного ИИ; инженерный полигон DDD / REST+WebSocket |
| Сценарий MAS | S3 (описанный проект: пакет требований и макет фронтенда уже есть; бэкенд в `src/` ещё не реализован) |
| Трекер | GitHub — URL не зафиксирован в репозитории; не выдумывать Issues |

## Стек

| Слой | Технология | Где зафиксировано |
| --- | --- | --- |
| Язык | Python 3.12+ | ТЗ §2.1 |
| UI | PySide6 (Qt for Python 6.x), пакет `src/frontend/` | ТЗ §2.3, `src/frontend/requirements.txt` |
| Прикладной слой | FastAPI + Uvicorn; DDD / Clean Architecture (`src/backend/`) | ТЗ §2.1, факт репозитория |
| Свой HTTP-сервер | да: REST + WebSocket (маршруты — по срезам `/app-layer`; каркас без endpoint’ов вне OpenAPI) | ТЗ §2.1, `requirements/openapi.yaml` |
| СУБД / NoSQL | Redis (сессии матчей, счётчики аналитики; не SQL) | ТЗ §2.2 |
| Тесты | pytest, pytest-asyncio, ruff, mypy (по ТЗ) | ТЗ §2.1 |
| Зависимости | `src/frontend/requirements.txt` (клиент); `src/backend/requirements.txt` (сервер); Compose — `docker-compose.yml` | факт репозитория |
| Конфиг процесса | `.env.example` → локальный `.env` (`REDIS_URL`, `HOST`, `PORT`, `REDIS_DATA_DIR`) | ТЗ §2.4 |

## Интеграции

| Система | Адрес / заметка | Источник |
| --- | --- | --- |
| OpenAPI preview | Swagger `:8080`, ReDoc `:8081` (`requirements/run-openapi-docs.bat`) | README |
| Будущий API | `http://localhost:8000` (каркас есть; игровые пути — следующие срезы `/app-layer`) | `openapi.yaml`, README |
| Redis | in-memory сессии с TTL; Compose: bind `${REDIS_DATA_DIR:-F:/Docker/Redis}` → `/data` | ТЗ §2.2, §2.4; `.env.example` |

## Владельцы артефактов

| Артефакт | Владелец | Команда |
| --- | --- | --- |
| ФТ | analyst | `/ft` |
| НФТ | architect | `/nft` |
| US | analyst | `/us` |
| UC | analyst | `/uc` |
| DDD | architect | `/ddd` |
| Словарь данных | architect | `/data-dictionary` |
| OpenAPI | architect | `/openai` |
| Vision | tech-writer | `/vision` |
| ТЗ ГОСТ | tech-writer | `/gost-3460289` |
| Макет UI | designer | `/ui-prototyping` |
| Рабочий UI | front-developer | `/frontend` |
| Бэкенд / API | back-developer | `/app-layer` |
| Тесты | tester | `/new-tests`, `/use-tests` |
| Гейт стадии | anatomist | `/qc-stage` |
| Оркестрация | pm | `/pm` |
