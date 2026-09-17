## 1. Структура папок и файлов проекта (Cursor)

После создания **новой папки** или **нового рабочего файла** проекта обновить `.cursor/rules/rule-structure.mdc` и эту копию. Экземпляры уже описанного шаблона именования (`us-NNN`, `uc-NNN`, `diagram-*-NNN`, `bpmn-NNN`) в список по одному не добавлять.

Корневые ориентиры:

* `README.md` — входной документ: как открыть окно фронтенда и документацию API, иерархия источников.
* `AGENTS.md` — общие инварианты агента и MAS.
* `.cursor/list-commands.md` — актуальный список команд Cursor, скиллов и агентов. При создании нового скилла, команды или агента ИИ обязан обновить этот файл.

Папки и рабочие файлы:

* `documentation` — файлы ТЗ и материалы разработчика (`specification-sea-battle-v1-1.md`, `project-structure-v1-1.md`, `mas-description.md`; структура синхронизируется с `.cursor/rules/rule-structure.mdc`).
* `requirements` — `functional-requirements.md`, `non-functional-requirements.md`, `answers-project.md` (закрытые ответы `Axxxx`), `glossary.md`, `domain-model.md`, `data-dictionary.md`, `openapi.yaml`; папки `user-stories` и `use-cases`; скрипты просмотра API: `run-openapi-docs.bat`, `preview-openapi.py`.
* `diagrams` — архитектурные и логические диаграммы (PlantUML / Mermaid / BPMN).
* `.cursor/skills` — промпты и инструкции для AI.
* `.cursor/rules` — правила для AI (`rule-*`, `role-*`).
* `.cursor/commands` — команды Cursor (`/pm`, `/ft`, `/nft`, `/us`, `/uc`, `/qc-ft-nft`, `/qc-us-uc`, `/qc-ddd`, `/qc-stage`, `/diagram-bpmn`, `/diagram-mermaid`, `/ddd`, `/data-dictionary`, `/ui-prototyping`, `/frontend`, `/app-layer`, `/openai`, `/new-tests`, `/use-tests`, `/vision`, `/gost-3460289`, `/pin-memory` и др.).
* `.cursor/agents` — Custom Agents MAS (`agent-pm`, `agent-analyst`, …).
* `src` — исходный код MVP: прототип фронтенда PySide6 (`src/frontend/`: `ui/`, `mock/`, `client/` HTTP и WebSocket к API; launcher `src/run-frontend.bat`); бэкенд FastAPI+Redis (`src/backend/`: `domain/`, `application/`, `infrastructure/`, `presentation/`, `Dockerfile`, `requirements.txt`; точка входа `main.py`).
* `docker-compose.yml` — корневой Compose MVP: сервисы `redis` + `backend` (:8000); поднимать только с разрешения пользователя.
* `.env.example` — образец несекретных переменных окружения бэкенда (`REDIS_URL`, `HOST`, `PORT`); рабочий `.env` в Git не коммитить.
* `tests` — автотесты (`test_should_*`), `conftest.py`, карта покрытия `tests/coverage.md`; прогон — `/use-tests` → `reports/test-run.md`.
* `reports` — отчёты MAS и QC: `agent-memory.md`, `project-config.md`, `pm-state.md`, `navigator.md`, `checklist.md` (срезы кода MVP), `templates/`, `incompatibility-ft-nft.md`, `incompatibility-us-uc.md`, `domain-model-review.md`, `review-report.md`, `test-run.md`; каркас `daily/`, `weekly/`, `commit-audit/`, `release/`.
* `artifacts` — Vision & Scope, ТЗ по ГОСТ и прочие артефакты вне `requirements`.
* `test-data` — зарезервирована на будущее; использовать только по прямому заданию разработчика; целевая папка.
* `legacy` — исходники и аналитика другого проекта; не в Git; агент работает с ней только по явной команде и прикреплению через `@` (исключено из репозитория и индексации).
* `old-skills` — скиллы из другого проекта; не в Git; агент работает с ней только по явной команде и прикреплению через `@` (исключено из репозитория и индексации).
* `imports` — копия чужого репозитория для переноса методологии; не в Git; тот же режим доступа, что у `legacy/` (`@` + явная команда).

---

## 2. Правила именования файлов (Naming Conventions)

* **User Stories (US):** префикс `us-` + трехзначный порядковый номер + название фичи через дефис. Пример: `us-001-auth.md`. Папка `requirements/user-stories/`. Реестр историй: `us-registry.md`. Роли и права: `list-us.md`.
* **Use Cases (UC):** префикс `uc-` + трехзначный порядковый номер + название сценария через дефис. Пример: `uc-001-login.md`. Папка `requirements/use-cases/`. Реестр и вопросы: `list-uc.md`.
* **Словарь данных:** `data-dictionary.md` в `requirements/`.
* **OpenAPI:** `openapi.yaml` в `requirements/`.
* **Диаграммы:** папка `diagrams/`. Если пользователь задал имя файла — сохранить его (например `diagram-dfd-001.md`, `diagram-class-001.md`). Если имя не задано — `diagram-mermaid-NNN.md`. BPMN 2.0: `bpmn-NNN.bpmn`. Новый предмет моделирования — новый номер; пересоздание той же диаграммы — тот же файл.
* **Отчёты:** папка `reports/`. Память агента: `agent-memory.md`. Конфиг MAS: `project-config.md`, `pm-state.md`, `navigator.md`. Срезы кода: `checklist.md`. QC ФТ/НФТ: `incompatibility-ft-nft.md`. QC US/UC: `incompatibility-us-uc.md`. Аудит DDD: `domain-model-review.md`. Гейт стадии: `review-report.md`. Прогон тестов: `test-run.md`. Карта покрытия автотестами: `tests/coverage.md`. Шаблоны: `reports/templates/`.
* **Скиллы:** префикс `skill-` + название в lowercase через дефис. Пример: `skill-ft.md`. Маршрутизаторы ролей: `skill-agent-<роль>.md`.
* **Правила:** префикс `rule-` + название или `role-` + роль. Примеры: `rule-structure.mdc`, `rule-answers-project.mdc`, `rule-python.mdc`, `role-pm.mdc`.
* **Агенты:** префикс `agent-` + название агента. Пример: `agent-analyst.md`. Файлы — в `.cursor/agents`.
* файл со списком всех команд запуска скиллов `list-commands.md`. Содержит актуальный список **slash-команд Cursor**, скиллов и агентов. Скрипты запуска продукта (`src/run-frontend.bat`, `requirements/run-openapi-docs.bat`) — не скиллы. При создании нового скилла, команды или агента ИИ обязан автоматически обновлять этот файл. Находится в папке `.cursor`.

---

## 3. Ограничения папок и файлов проекта

* legacy, old-skills, imports — строго исключены из Git и из индексации ИИ (`.gitignore`, `.cursorignore`). Агенту запрещено самостоятельно открывать, искать, читать или править эти папки. Разрешено только при одновременном выполнении обоих условий: (1) явная команда разработчика в чате; (2) прикрепление папки или файла из них через `@`. Без `@` или без явной команды — не трогать.
* diagrams — только текстовые форматы диаграмм (.puml для PlantUML, блоки кода в .md для Mermaid, BPMN 2.0 XML для импорта в bpmn.io). Бинарные файлы и картинки не используются для актуализации, но могут создаваться по запросу разработчика.
* **Markdown и fenced `text`:** в любых `.md` файлах проекта **запрещено** использовать обёртку ` ```text ` … ` ``` ` (и пустой fence ` ``` ` без языка для длинных цитат/шаблонов, если цель — «просто текст»). Причина: в MarkText и похожих редакторах появляется горизонтальная прокрутка, файлы неудобно читать. Пиши обычным markdown-текстом. Допустимы fence с осмысленным языком там, где нужен код/диаграмма (`mermaid`, `puml`, фрагменты исходников и т.п.), но **не** `text`. В User Stories критерии приёмки (Gherkin) — тоже без fence (`Given` / `When` / `Then` обычным текстом).
