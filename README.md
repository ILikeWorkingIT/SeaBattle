# Sea Battle

Клиент-серверная игра «Морской бой» в режиме игрок против серверного ИИ (PvE). Проект — инженерный полигон: DDD / Clean Architecture, REST + WebSocket, десктоп-клиент и контейнеризированный бэкенд.

Стек по ТЗ: Python 3.12+, FastAPI, Redis, PySide6, Docker.

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

## Входные документы

- `documentation/specification-sea-battle-v1-1.md` — техническое задание (правила игры, ИИ, стек, языки).
- `documentation/project-structure-v1-1.md` — структура папок и правила именования файлов (синхронизируется с `.cursor/rules/rule-structure.mdc`).

**Иерархия источников:** предварительное ТЗ — в `documentation/`; уточнения — в `requirements/answers-project.md` (`Axxxx`) и согласованных ФТ/НФТ. При конфликте с предварительным ТЗ приоритет у `Axxxx` и согласованных требований. Поведение агента — в `AGENTS.md`; память проекта — в `reports/agent-memory.md`.

## Структура папок

| Папка / файл | Назначение | Статус | Коммит / репозиторий | Индексация ИИ |
| --- | --- | --- | --- | --- |
| `documentation` | ТЗ и материалы разработчика | есть | да | да |
| `requirements` | `functional-requirements.md`, `non-functional-requirements.md`, `answers-project.md` (`Axxxx`), `glossary.md`; целевые: `domain-model.md`, `user-stories/`, `use-cases/` | есть (базовые файлы) | да | да |
| `diagrams` | текстовые диаграммы (PlantUML / Mermaid / BPMN) | целевая | да (текст) | да (текст; картинки и бинарники — нет) |
| `.cursor/skills` | промпты и инструкции для AI | есть | да | да |
| `.cursor/rules` | правила для AI | есть | да | да |
| `.cursor/commands` | команды Cursor (`/ft`, `/nft`, `/qc-ft-nft`, `/pin-memory`) | есть | да | да |
| `src` | исходный код MVP, скрипты, настройки | целевая | да | да |
| `reports` | отчёты; в т.ч. `agent-memory.md` | есть | да | да |
| `artifacts` | артефакты вне `requirements` | целевая | да | да |
| `tests` | автотесты | целевая | да | да |
| `test-data` | зарезервирована; только по прямому заданию разработчика | целевая | да | да |
| `legacy` | исходники и аналитика другого проекта; только по прямому заданию | — | нет | нет |
| `old-skills` | скиллы из другого проекта; только по прямому заданию | — | нет | нет |

Корневые ориентиры: `AGENTS.md` (правила агента), `.cursor/list-commands.md` (список команд и скиллов).

`legacy/` и `old-skills/` исключены в `.gitignore` и `.cursorignore`. Не читать их самостоятельно, если разработчик явно не прикрепил файл через `@`.
