# Sea Battle

Клиент-серверная игра «Морской бой»: человек против серверного ИИ (PvE). Инженерный полигон: пакет требований, DDD / Clean Architecture, REST + WebSocket, десктоп PySide6, FastAPI + Redis в Docker.

**За 30 секунд:** игрок в окне на хосте; API на `:8000`; живые выстрелы только по WebSocket; Redis держит до трёх сессий с idle TTL 30 минут и глобальную статистику; heatmap на клиент не уходит. MVP **v1.0.0** (ветка `main`, тег `v1.0.0`) без логина, PvP и ручной расстановки.

Витрина для скрининга (кейс, C4, ADR, сценарий демо): [artifacts/portfolio/](artifacts/portfolio/). English: [README.en.md](README.en.md).

Стек: Python 3.12+, FastAPI, Redis, PySide6, Docker.

Мультиагентная оболочка Cursor (MAS) — способ разработки, не суть продукта. Вход для агентов: `/pm`. Описание — `documentation/mas-description.md`; стек — `reports/project-config.md`; команды — `.cursor/list-commands.md`.

## Как открыть окно Фронтенда

Прототип — десктопное окно PySide6. Запуск из чата Cursor окно на рабочий стол не выводит (скрытая сессия).

1. В проводнике откройте `src` и дважды щёлкните `run-frontend.bat`.
2. Запасной способ — обычный PowerShell (не терминал агента в чате):

```powershell
cd e:\Cursor\SeaBattle\src
$env:PYTHONPATH = "e:\Cursor\SeaBattle\src"
python -m frontend
```

Заголовок окна: **Sea Battle — PvE**. Нужны Python 3.12+ и `PySide6` (`pip install -r src/frontend/requirements.txt`).

## Как открыть документацию API

Контракт: `requirements/openapi.yaml` (OpenAPI 3.0.3). Это спецификация, не работающий бэкенд.

`servers.url` `http://localhost:8000` — живой FastAPI / Uvicorn (**не** путать с просмотрщиками YAML на 8080/8081). Try it out в Swagger заработает только если поднят сервис `backend` (Compose, см. ниже). Без сервера будет ошибка соединения — это не дефект контракта.

Просмотр документации (обычный Chrome или Edge, не Simple Browser Cursor):

- Swagger UI: http://127.0.0.1:8080/
- ReDoc: http://127.0.0.1:8081/

Если просмотрщики ещё не запущены: в проводнике откройте `requirements` и дважды щёлкните `run-openapi-docs.bat`. Если 8080 или 8081 заняты, скрипт берёт следующие свободные порты и печатает фактические URL в окне консоли.

Запасной способ — обычный PowerShell (не терминал агента в чате):

```powershell
cd e:\Cursor\SeaBattle\requirements
python preview-openapi.py
```

## Как поднять API (Redis + backend)

Канон инфраструктуры: корневой `docker-compose.yml` (сервисы `redis` и `backend` на порту **8000**). Данные Redis на хосте по умолчанию — `F:/Docker/Redis`; другой диск или папка — `REDIS_DATA_DIR` в `.env` (образец `.env.example`, рабочий `.env` в Git не коммитить).

Агент Cursor **не** поднимает Docker, пока вы явно не разрешили. Запуск — в обычном PowerShell (не терминал агента в чате), из корня репозитория:

```powershell
docker compose up --build
```

Остановка: `docker compose down`. Локальный Uvicorn без Compose допустим, если Redis уже доступен; канон — Compose.

Подробный запуск на **другом компьютере без Cursor** (что поставить, какие контейнеры, проверка API, окно игры): [result/instruction.md](result/instruction.md).

## Входные документы

- `artifacts/vision-scope.md` — Vision & Scope (черновик до «согласую Vision»).
- `artifacts/tz-gost-seabattle.md` — ТЗ по ГОСТ 34.602-89 (черновик до «согласую ТЗ»).
- `artifacts/portfolio/` — витрина для собеседования (кейс, C4, ADR, сценарий демо).
- `documentation/specification-sea-battle-v1-1.md` — техническое задание (правила игры, ИИ, стек, языки).
- `documentation/mas-description.md` — мультиагентная система Cursor (роли, гейты, `/pm`).
- `documentation/project-structure-v1-1.md` — структура папок и правила именования файлов (синхронизируется с `.cursor/rules/rule-structure.mdc`).

**Иерархия источников:** предварительное ТЗ — в `documentation/`; уточнения — в `requirements/answers-project.md` (`Axxxx`) и согласованных ФТ/НФТ. При конфликте с предварительным ТЗ приоритет у `Axxxx` и согласованных требований. Поведение агента — в `AGENTS.md`; память проекта — в `reports/agent-memory.md`.

## Структура папок

| Папка / файл | Назначение | Статус | Коммит / репозиторий | Индексация ИИ |
| --- | --- | --- | --- | --- |
| `documentation` | ТЗ, MAS, материалы разработчика | есть | да | да |
| `requirements` | `functional-requirements.md`, `non-functional-requirements.md`, `answers-project.md` (`Axxxx`), `glossary.md`, `domain-model.md`, `data-dictionary.md`, `openapi.yaml`; `user-stories/`, `use-cases/`; `run-openapi-docs.bat`, `preview-openapi.py` | есть | да | да |
| `diagrams` | текстовые диаграммы (PlantUML / Mermaid / BPMN) | есть | да (текст) | да (текст; картинки и бинарники — нет) |
| `.cursor/skills` | промпты и инструкции для AI | есть | да | да |
| `.cursor/rules` | правила для AI | есть | да | да |
| `.cursor/commands` | slash-команды Cursor (`/pm`, `/ft`, `/openai`, `/frontend`, `/app-layer` и др.) | есть | да | да |
| `.cursor/agents` | файлы агентов MAS | есть | да | да |
| `src` | MVP: `frontend/` (PySide6, `run-frontend.bat`), `backend/` (FastAPI+Redis, `main.py`) | есть | да | да |
| `docker-compose.yml` | Compose MVP: `redis` + `backend` (:8000); поднимать только с разрешения | есть | да | да |
| `.env.example` | образец несекретных переменных (`REDIS_URL`, `HOST`, `PORT`, `REDIS_DATA_DIR`); рабочий `.env` не коммитить | есть | да | да |
| `reports` | отчёты MAS/QC: `agent-memory.md`, `project-config.md`, `pm-state.md`, `navigator.md`, `checklist.md`, шаблоны | есть | да | да |
| `artifacts` | артефакты вне `requirements` (витрина портфолио, Vision, ГОСТ) | есть (`portfolio/`) | да | да |
| `result` | инструкция внешнего запуска без Cursor (`instruction.md`) | есть | да | да |
| `tests` | автотесты (`test_should_*`), `coverage.md`; прогон — `/use-tests` → `reports/test-run.md` | есть | да | да |
| `test-data` | зарезервирована; только по прямому заданию разработчика | целевая | да | да |
| `legacy` | исходники и аналитика другого проекта; только по явной команде + `@` | — | нет | нет |
| `old-skills` | скиллы из другого проекта; только по явной команде + `@` | — | нет | нет |
| `imports` | копия чужого репозитория для переноса методологии; только по явной команде + `@` | — | нет | нет |

Корневые ориентиры: `AGENTS.md` (правила агента и MAS), `.cursor/list-commands.md` (список команд, скиллов и агентов).

`legacy/`, `old-skills/` и `imports/` исключены в `.gitignore` и `.cursorignore`. Агент работает с ними только при явной команде и прикреплении через `@`.
