# Список команд

Актуальный индекс slash-команд Cursor, скиллов и агентов. Обновлять при создании нового скилла, агента или команды.

Режимы, SOP и запреты — **в скилле**, на который указывает команда. Этот файл не дублирует плейбук.

Скиллы с `disable-model-invocation: true` сами не подхватываются: нужен slash, агент-маршрутизатор или явная просьба открыть скилл. В сценарии S5 (обычный чат) без команды исполнитель может скилл не прочитать.

**Не путать:** сценарий **S5** (обычный чат, оркестрация ПМ на паузе) ≠ срез чеклиста **`S-05`**.

| Команда | Файл | Скилл | Назначение |
| --- | --- | --- | --- |
| `/pm` | `.cursor/commands/pm.md` | `skill-agent-pm` | Точка входа MAS: статус / конвейер **одного** среза из `reports/checklist.md`. Не `/full-cycle` |
| `/pin-memory` | `.cursor/commands/pin-memory.md` | нет отдельного скилла (алгоритм в команде) | Запись устойчивого вывода в `reports/agent-memory.md` |
| `/vision` | `.cursor/commands/vision.md` | `skill-vision` | Vision & Scope (`tech-writer`) → `artifacts/vision-scope.md` |
| `/gost-3460289` | `.cursor/commands/gost-3460289.md` | `skill-gost-3460289` | ТЗ по ГОСТ 34.602-89 (`tech-writer`) → `artifacts/tz-gost-<код>.md` |
| `/ft` | `.cursor/commands/ft.md` | `skill-ft` | Написать или обновить ФТ. Аудит без написания → `/qc-ft-nft` |
| `/nft` | `.cursor/commands/nft.md` | `skill-nft` | Написать или обновить НФТ. Аудит без написания → `/qc-ft-nft` |
| `/us` | `.cursor/commands/us.md` | `skill-us` | Написать или обновить User Stories. Аудит без написания → `/qc-us-uc` |
| `/uc` | `.cursor/commands/uc.md` | `skill-uc` | Написать или обновить Use Cases. Аудит без написания → `/qc-us-uc` |
| `/qc-ft-nft` | `.cursor/commands/qc-ft-nft.md` | `skill-quality-control-ft-nft` | QC ФТ и НФТ |
| `/qc-us-uc` | `.cursor/commands/qc-us-uc.md` | `skill-quality-control-us-uc` | QC US и UC |
| `/diagram-bpmn` | `.cursor/commands/diagram-bpmn.md` | `skill-diagram-bpmn` | BPMN 2.0 для bpmn.io |
| `/diagram-mermaid` | `.cursor/commands/diagram-mermaid.md` | `skill-diagram-mermaid` | Mermaid: flowchart, DFD, class, sequence, C4 |
| `/ddd` | `.cursor/commands/ddd.md` | `skill-ddd` | Доменная модель. В конце **сам** один проход `skill-quality-control-ddd` (режим «после /ddd»). Отдельную команду `/qc-ddd` не ждать и не предлагать |
| `/qc-ddd` | `.cursor/commands/qc-ddd.md` | `skill-quality-control-ddd` | Самостоятельный аудит **уже лежащей** модели (не хвост `/ddd`) |
| `/data-dictionary` | `.cursor/commands/data-dictionary.md` | `skill-data-dictionary` | Словарь данных; после записи — гейт §7 скилла |
| `/ui-prototyping` | `.cursor/commands/ui-prototyping.md` | `skill-ui-prototyping` | Визуальный макет окна (навигация без доменной логики) |
| `/frontend` | `.cursor/commands/frontend.md` | `skill-frontend-developer` | Рабочий desktop UI (PySide6). Макет — `/ui-prototyping` |
| `/app-layer` | `.cursor/commands/app-layer.md` | `skill-app-layer` | Бэкенд FastAPI + Redis в `src/backend/`. Тесты не пишет |
| `/openai` | `.cursor/commands/openai.md` | `skill-openai` | OpenAPI YAML (не вендор OpenAI) |
| `/new-tests` | `.cursor/commands/new-tests.md` | `skill-new-tests` | Новые автотесты. Прогон в том же ходе не делать |
| `/use-tests` | `.cursor/commands/use-tests.md` | `skill-use-tests` | Прогон → `reports/test-run.md` |
| `/qc-stage` | `.cursor/commands/qc-stage.md` | `skill-agent-anatomist` | Гейт стадии: `stage-id` → `reports/review-report.md` |

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

## Ловушки (не копировать плейбук скилла)

- **`/pm`:** конвейер — по «запускай S-NN» / «запускай срез» после предложения среза. Голое «согласен» без id и без только что предложенного среза **не** стартует конвейер (можно спутать с QC / Vision). Нет `/full-cycle`. Прямые slash — **сценарий S5**, не срез `S-05`.
- **`/ddd` vs `/qc-ddd`:** после `/ddd` QC уже внутри скилла написания. Самостоятельный `/qc-ddd` — только аудит готового файла.
- **«согласен»:** у `/pm` — только если это ответ на предложение среза (лучше «запускай S-NN»). У QC / словаря / Vision — перенос ответов в файлы. Утверждение этапа — «утверждаю» / «срез согласован», не «согласен».
- **Тесты:** код бэка/фронта — `/app-layer` / `/frontend`. Тесты пишет `/new-tests`, гоняет `/use-tests`. В одном ходе код и тесты не смешивать.
- **`/qc-stage`:** `stage-id` = имя команды без `/` **или** заголовок среза `S-NN` из чеклиста. Неизвестное имя — fail.
