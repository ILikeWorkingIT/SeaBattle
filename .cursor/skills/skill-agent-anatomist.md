---
name: skill-agent-anatomist
description: >-
  Universal quality gate /qc-stage. Reads stage-id from reports/pm-state.md,
  maps it to .cursor/list-commands.md, returns a structured report to PM.
  Existing /qc-ft-nft /qc-us-uc /qc-ddd are not replaced.
disable-model-invocation: true
owner: anatomist
---

# Скилл агента anatomist — `/qc-stage`

Универсальный второй проход. Точечные QC не копируй: если стадия — уже существующий QC, выполни его скилл.

## Шаг 1. Считать стадию

Открой `reports/pm-state.md`. Возьми `stage-id` (строка `- stage-id:`).

- Если в запросе (`$1` или явная фраза) передан `stage-id` — он важнее файла. Обнови **только** строку `- stage-id:` в `pm-state.md`. Поля `approval`, `status` и `Stage: … APPROVED` не трогай.
- Если в запросе id нет, а в файле `stage-id` пустой — остановись. Верни ПМ: «stage-id не задан». Отчёт не выдумывай.

## Шаг 2. Сопоставить со списком команд

Открой `.cursor/list-commands.md`. Найди команду, у которой имя без `/` совпадает с `stage-id`, либо строку таблицы, где `stage-id` явно указан.

Нормализация: `qc-ft-nft` → `/qc-ft-nft`. Не путать с несуществующим `/qc-nf-nft`.

Срез чеклиста: `stage-id` совпадает с заголовком среза в `reports/checklist.md` (`S-01` и любой другой `S-` + суффикс из этого файла). Команды в таблице нет. Читай секцию этого среза. Команда гейта = универсальный чек-лист ниже, плюс критерии «срез готов».

Если команды нет в списке и это не id среза из чеклиста — вердикт `fail`, замечание major: неизвестный `stage-id`.

## Шаг 3. Выбрать процедуру

| stage-id | Процедура |
| --- | --- |
| `qc-ft-nft` | Выполни `.cursor/skills/skill-quality-control-ft-nft.md` (режим по тексту запроса ПМ). Не пиши ФТ «заодно». |
| `qc-us-uc` | Выполни `skill-quality-control-us-uc`. |
| `qc-ddd` | Выполни `skill-quality-control-ddd`. |
| `ft`, `nft`, `us`, `uc`, `ddd`, `data-dictionary`, `openai`, `vision`, `gost-3460289` | Универсальный чек-лист + существование артефакта команды из `list-commands.md`. Не запускай скилл написания. |
| `frontend`, `app-layer`, `ui-prototyping`, `new-tests`, `use-tests` | Универсальный чек-лист + критерий из команды/чеклиста. Код не меняй. |
| `S-*` (id среза из `reports/checklist.md`) | Критерии «срез готов» этой секции + универсальный чек-лист. Не путать со **сценарием S5**. |
| любая другая команда из `list-commands.md` (`diagram-bpmn`, `pin-memory`, `pm`, `qc-stage`, …) | Универсальный чек-лист + существование артефакта (если у команды он есть). Код и точечные скиллы написания не запускай. |

## Шаг 4. Универсальный чек-лист

Заполни по шаблону `reports/templates/review-gate-report.template.md`. Сохрани в `reports/review-report.md` (не затирай точечные отчёты `incompatibility-*.md` и `domain-model-review.md`).

Проверь:

1. Ожидаемый артефакт команды существует по пути из `list-commands.md` / скилла.
2. Нет правок вне Input Manifest исполнителя (по диффу или списку путей в задаче ПМ — не обвиняй без следа).
3. Точечный скилл не затёрт (сравни, что команда всё ещё указывает на тот же файл скилла).
4. Критерии стадии проверяемы (нет «быстро» без меры; для среза — пункты «срез готов»).

Уровни: `critical` — артефакта нет или сломан канон; `major` — гейт нельзя считать пройденным; `minor` — known issue для `pm-state.md`.

## Шаг 5. Вердикт ПМ

- Есть critical или major → `fail`. Глобальный этап не двигается.
- Иначе → `pass`. В чат ПМ: путь отчёта, вердикт, список critical/major/minor. Не пиши APPROVED.
