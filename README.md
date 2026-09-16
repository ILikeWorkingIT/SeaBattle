# Sea Battle

Клиент-серверная игра «Морской бой» в режиме игрок против серверного ИИ (PvE). Проект — инженерный полигон: DDD / Clean Architecture, REST + WebSocket, десктоп-клиент и контейнеризированный бэкенд.

Стек по ТЗ: Python 3.12+, FastAPI, Redis, PySide6, Docker.

Мультиагентная оболочка Cursor (MAS): предпочтительный вход — `/pm`. Описание — `documentation/mas-description.md`; стек для агентов — `reports/project-config.md`; команды — `.cursor/list-commands.md`.

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

`servers.url` `http://localhost:8000` — будущий FastAPI / Uvicorn. Сейчас этот порт не слушает API: Try it out в Swagger будет с ошибкой соединения.

Просмотр документации (обычный Chrome или Edge, не Simple Browser Cursor):

- Swagger UI: http://127.0.0.1:8080/
- ReDoc: http://127.0.0.1:8081/

Если просмотрщики ещё не запущены: в проводнике откройте `requirements` и дважды щёлкните `run-openapi-docs.bat`. Если 8080 или 8081 заняты, скрипт берёт следующие свободные порты и печатает фактические URL в окне консоли.

Запасной способ — обычный PowerShell (не терминал агента в чате):

```powershell
cd e:\Cursor\SeaBattle\requirements
python preview-openapi.py
```

## Входные документы

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
| `.cursor/commands` | команды Cursor (`/pm`, `/ft`, `/openai`, `/frontend`, `/app-layer` и др.) | есть | да | да |
| `.cursor/agents` | файлы агентов MAS | есть | да | да |
| `src` | исходный код MVP, скрипты, настройки (`run-frontend.bat`, пакет `frontend`) | есть | да | да |
| `reports` | отчёты: `agent-memory.md`, `project-config.md`, `pm-state.md`, `navigator.md`, QC, шаблоны MAS | есть | да | да |
| `artifacts` | артефакты вне `requirements` (Vision, ГОСТ) | целевая | да | да |
| `tests` | автотесты | целевая | да | да |
| `test-data` | зарезервирована; только по прямому заданию разработчика | целевая | да | да |
| `legacy` | исходники и аналитика другого проекта; только по явной команде + `@` | — | нет | нет |
| `old-skills` | скиллы из другого проекта; только по явной команде + `@` | — | нет | нет |
| `imports` | копия чужого репозитория для переноса методологии; только по явной команде + `@` | — | нет | нет |

Корневые ориентиры: `AGENTS.md` (правила агента и MAS), `.cursor/list-commands.md` (список команд, скиллов и агентов).

`legacy/`, `old-skills/` и `imports/` исключены в `.gitignore` и `.cursorignore`. Агент работает с ними только при явной команде и прикреплении через `@`.
