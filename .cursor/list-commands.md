# Список команд

Актуальный список команд запуска скиллов и агентов. Обновлять при создании нового скилла, агента или команды.

| Команда | Файл | Назначение |
| --- | --- | --- |
| `/pm` | `.cursor/commands/pm.md` | Точка входа MAS: роль `pm`, скилл `.cursor/skills/skill-agent-pm.md`. Сверяет `project-config.md` / `pm-state.md`, предлагает или стартует один этап. Не `/full-cycle` |
| `/pin-memory` | `.cursor/commands/pin-memory.md` | Быстро сохранить устойчивый вывод из чата в `reports/agent-memory.md` |
| `/vision` | `.cursor/commands/vision.md` | Vision & Scope: роль `tech-writer`, скилл `.cursor/skills/skill-vision.md`; по умолчанию `artifacts/vision-scope.md` |
| `/gost-3460289` | `.cursor/commands/gost-3460289.md` | ТЗ по ГОСТ 34.602-89: роль `tech-writer`, скилл `.cursor/skills/skill-gost-3460289.md`; `artifacts/tz-gost-<код>.md` |
| `/ft` | `.cursor/commands/ft.md` | Написать или обновить функциональные требования по `.cursor/skills/skill-ft.md` |
| `/nft` | `.cursor/commands/nft.md` | Написать или обновить нефункциональные требования по `.cursor/skills/skill-nft.md` |
| `/us` | `.cursor/commands/us.md` | Написать или обновить User Stories, роли и права по `.cursor/skills/skill-us.md` |
| `/uc` | `.cursor/commands/uc.md` | Написать или обновить Use Cases (Cockburn) по `.cursor/skills/skill-uc.md` |
| `/qc-ft-nft` | `.cursor/commands/qc-ft-nft.md` | Проверить качество ФТ и НФТ по `.cursor/skills/skill-quality-control-ft-nft.md` |
| `/qc-us-uc` | `.cursor/commands/qc-us-uc.md` | Проверить качество US и UC по `.cursor/skills/skill-quality-control-us-uc.md` |
| `/diagram-bpmn` | `.cursor/commands/diagram-bpmn.md` | Моделировать бизнес-процесс в BPMN 2.0 для bpmn.io по `.cursor/skills/skill-diagram-bpmn.md` |
| `/diagram-mermaid` | `.cursor/commands/diagram-mermaid.md` | Mermaid: flowchart, DFD, classDiagram, sequenceDiagram, C4 по `.cursor/skills/skill-diagram-mermaid.md` |
| `/ddd` | `.cursor/commands/ddd.md` | Доменная модель (DDD) по `.cursor/skills/skill-ddd.md`; в конце обязательно `/qc-ddd` |
| `/qc-ddd` | `.cursor/commands/qc-ddd.md` | Контроль качества DDD-модели по `.cursor/skills/skill-quality-control-ddd.md` |
| `/data-dictionary` | `.cursor/commands/data-dictionary.md` | Словарь данных по `.cursor/skills/skill-data-dictionary.md`; после записи обязателен гейт |
| `/ui-prototyping` | `.cursor/commands/ui-prototyping.md` | Визуальный макет окна фронтенда (навигация без доменной логики) по `.cursor/skills/skill-ui-prototyping.md` |
| `/frontend` | `.cursor/commands/frontend.md` | Рабочий desktop UI (PySide6) по `.cursor/skills/skill-frontend-developer.md`; макет — `/ui-prototyping` |
| `/app-layer` | `.cursor/commands/app-layer.md` | Прикладной слой и HTTP/WS API (FastAPI, Redis) по `.cursor/skills/skill-app-layer.md` |
| `/openai` | `.cursor/commands/openai.md` | OpenAPI-спецификация (YAML, Swagger UI + ReDoc) по `.cursor/skills/skill-openai.md` |
| `/new-tests` | `.cursor/commands/new-tests.md` | Новые автотесты (API и/или UI) по `.cursor/skills/skill-new-tests.md`; прогон в том же ходе не делать |
| `/use-tests` | `.cursor/commands/use-tests.md` | Прогон автотестов по `.cursor/skills/skill-use-tests.md`; отчёт `reports/test-run.md` |
| `/qc-stage` | `.cursor/commands/qc-stage.md` | Универсальный гейт стадии: `stage-id` из `reports/pm-state.md` → отчёт `reports/review-report.md` по `.cursor/skills/skill-agent-anatomist.md` |

## Агенты MAS

Файлы в `.cursor/agents/`. Канон — Custom Agents / subagents Cursor. Предпочтительный вход — `pm`.

| Агент | Файл | Скилл-маршрутизатор | Правило |
| --- | --- | --- | --- |
| `pm` | `.cursor/agents/agent-pm.md` | `skill-agent-pm` | `role-pm.mdc` |
| `analyst` | `.cursor/agents/agent-analyst.md` | `skill-agent-analyst` | `role-analyst.mdc` |
| `architect` | `.cursor/agents/agent-architect.md` | `skill-agent-architect` | `role-architect.mdc` |
| `tech-writer` | `.cursor/agents/agent-tech-writer.md` | `skill-agent-tech-writer` | `role-tech-writer.mdc` |
| `anatomist` | `.cursor/agents/agent-anatomist.md` | `skill-agent-anatomist` | `role-anatomist.mdc` |
| `designer` | `.cursor/agents/agent-designer.md` | `skill-agent-designer` | `role-designer.mdc` |
| `front-developer` | `.cursor/agents/agent-front-developer.md` | `skill-agent-front-developer` | `role-front-developer.mdc` |
| `back-developer` | `.cursor/agents/agent-back-developer.md` | `skill-agent-back-developer` | `role-back-developer.mdc` |
| `tester` | `.cursor/agents/agent-tester.md` | `skill-agent-tester` | `role-tester.mdc` |

## Режимы `/pm`

Отдельной подкоманды нет: режим выбирается по содержимому запроса.

**Статус** — пустой `/pm`, «что дальше». ПМ читает config и navigator, предлагает `stage-id` и команду. Код не пишет. `/qc-stage` не запускает.

**Старт этапа** — в запросе срез или команда. ПМ пишет `stage-id` и назначает исполнителя. Чужие скиллы в том же ходе — только если явно попросили выполнить работу, не только план.

**Утверждение** — «утверждаю» / «принимаю этап». ПМ пишет `Stage: <id>: APPROVED`. Следующий глобальный этап сам не начинает.

Нет `/full-cycle`. Прямые `/ft`, `/frontend` по-прежнему допустимы.

## Режимы `/vision`

Отдельной подкоманды нет.

**Создание** — типичный `/vision`. Исполнитель — `tech-writer`. Файл `artifacts/vision-scope.md` по `skill-vision`.

**Правка** — точечное уточнение разделов. Канон — из ФТ/`Axxxx`, если есть.

**Перенос ответов** — закрытые пары в `answers-project.md` с кодом `VS`. Согласование документа: «согласую Vision» / «принимаю Vision & Scope» (не путать с «утверждаю» этапа).

## Режимы `/gost-3460289`

Отдельной подкоманды нет.

**Создание** / **реструктуризация** / **стилизация** / **аудит** / **перенос ответов** — по `skill-gost-3460289`. Код ответов в базе — `TZ`. Согласование: «согласую ТЗ» / «принимаю техническое задание».

## Режимы `/qc-ft-nft` и `/qc-us-uc`

Отдельной подкоманды нет: режим выбирается по содержимому запроса.

**Отчёт без правок** (шаги 1–2 скилла) — когда ещё нечего вносить. Типично: пустой `/qc-ft-nft` или `/qc-us-uc`, «проверь ФТ/НФТ», «проверь US/UC», «аудит». Агент пишет отчёт, колонку «ответ» оставляет пустой, файлы требований / US / UC не меняет.

**Перенос ответов** (шаг 3 скилла) — когда ответы уже есть: в чате («согласен», «да», текст по пунктам), в колонке «ответ» отчёта или явная фраза «обработай ответы» / «внеси». Агент правит файлы, записывает закрытые пары в `requirements/answers-project.md` (`Axxxx`), повторный QC по тем же правкам не предлагает.

Практический цикл:

1. `/qc-ft-nft` или `/qc-us-uc` — получить отчёт.
2. Ответить в чате или в таблице отчёта.
3. Снова та же QC-команда и в том же сообщении ответы либо «обработай ответы из отчёта».

Для `/qc-us-uc`: «проверь и исправь» в одном запросе — сначала отчёт, сразу правятся только пункты типа «Исправление» (данных в источниках уже достаточно). Строки-вопросы без ответа догадкой не закрываются.

Если в одном сообщении и «проверь», и ответы — сначала перенос ответов, новый полный аудит сам не начинается. Новый QC — только по явной просьбе или если появились новые требования / истории / сценарии сверх того отчёта.

## Режимы `/qc-ddd`

Отдельной подкоманды нет: режим выбирается по содержимому запроса.

**Отчёт без правок** — когда ещё нечего вносить в модель. Типично: пустой `/qc-ddd`, «проверь модель», «аудит DDD». Агент пишет `reports/domain-model-review.md`, файл `requirements/domain-model.md` не меняет.

**Перенос §4** — когда есть явное согласие: в чате («согласен», «внеси», «примени §4») или просьба обработать выводы отчёта. Агент переносит в модель только разрешённый набор из скилла, записывает закрытые пары в `requirements/answers-project.md` (`Axxxx`, код `DDD`), повторный `/qc-ddd` по тем же правкам не предлагает.

Практический цикл самостоятельного QC:

1. `/qc-ddd` — получить отчёт.
2. Ответить в чате (согласие на §4 или точечные ответы).
3. Снова `/qc-ddd` в том же сообщении с согласием либо «обработай ответы из отчёта».

После `/ddd` отдельную команду `/qc-ddd` ждать не нужно: скилл написания модели сам выполняет один проход QC в режиме «после /ddd».

Если в одном сообщении и «проверь», и ответы — сначала перенос ответов, новый полный аудит сам не начинается. Новый QC — только по явной просьбе или если появились новые требования / истории / сценарии сверх того отчёта.

## Режимы `/ui-prototyping`

Отдельной подкоманды нет: режим выбирается по содержимому запроса. Это одна команда, не три.

**Создание** — «сделай макет», клиента ещё нет, или явная пересборка / упрощение до визуального макета. Агент пишет UI со **статичным** mock: внешний вид + навигация (меню, кнопки → окна/экраны, вкладки, язык). Без доменной логики и «игры». В конце чата: где код, какой экран, как открыть окно **самим** (не из терминала агента в чате).

**Правка** — макет уже есть, точечная просьба («текст жёлтый», баг кнопки). Агент меняет только это и напоминает перезапустить тем же способом. Новый макет и README с нуля не делает. Доменную логику не возвращает.

**Только запуск** — «не вижу окно», «как открыть». Код не трогает. В чате только способ: launcher в проводнике (`src/run-frontend.bat`).

## Режимы `/frontend`

Отдельной подкоманды нет.

**Фича** — рабочий экран / кнопка / стейт по ФТ. Код в `src/frontend/` (PySide6). Тесты в том же ходе не пишет и не гоняет.

**Баг** — регрессия интерфейса, гонка, блокировка. Минимальный дифф.

**Полировка** — вид без смены правил ФТ. Селекторы (`self.*`, `objectName`) не ломает.

Макет без функционала — `/ui-prototyping`. FastAPI / Redis / heatmap — `/app-layer`. После правки предлагает `/new-tests` и `/use-tests` отдельно.

## Режимы `/app-layer`

Отдельной подкоманды нет.

**Фича** — служба / endpoint / use case по ФТ / OpenAPI. Код в `src/backend/`. GUI не трогает. Unit-тесты без GUI — в том же ходе по скиллу. `/use-tests` не запускает.

**Баг** — сессия Redis, WS, инвариант поля. Минимальный дифф.

Виджеты — `/frontend`. Макет — `/ui-prototyping`. Только YAML контракта — `/openai`.

## Режимы `/new-tests`

Отдельной подкоманды нет.

**Дополнение** — «напиши тесты». Добавляет пробелы в `tests/`. Продуктовый код не меняет.

**Инвентаризация** — «каких тестов не хватает». Файлы не создаёт.

**Обновление устаревших** — правит ложные эталоны.

После дополнения предлагает `/use-tests` и не запускает её в том же прогоне.

## Режимы `/use-tests`

Отдельной подкоманды нет.

**Прогон** — гоняет набор, пишет `reports/test-run.md`. Код не меняет.

**Прогон и исправление** — «исправь»: сначала отчёт, затем только `product_bug`. Лимит: 2 попытки на баг, 4 полных прогона.

**Повтор** — «перепрогони».

Нет тестов — предлагает `/new-tests`.

## Режимы `/qc-stage`

Отдельной подкоманды нет.

**Гейт текущей стадии** — типичный `/qc-stage`. Анатомист читает `stage-id` из `reports/pm-state.md`, пишет `reports/review-report.md`. Этап не утверждает.

**Явный stage-id** — в запросе указан id. Он важнее поля в `pm-state.md`. Анатомист обновляет только строку `- stage-id:`. Не ставит `APPROVED`.

Если `stage-id` = `qc-ft-nft` / `qc-us-uc` / `qc-ddd` — выполни соответствующий точечный QC-скилл.
