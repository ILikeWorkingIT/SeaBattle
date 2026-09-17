# Универсальный гейт стадии

Прочитай и выполни `.cursor/skills/skill-agent-anatomist.md` целиком. Команда `/qc-stage` запускает этот скилл. Роль-исполнитель — anatomist.

## Цель этапа

Второй проход по текущей стадии: сопоставить `stage-id` со списком команд и вернуть ПМ вердикт с чек-листом.

## Роль-исполнитель

`anatomist` (`.cursor/agents/agent-anatomist.md`).

## Input manifest

- `reports/pm-state.md` (поле `stage-id`)
- `.cursor/list-commands.md`
- `reports/project-config.md`
- `reports/templates/review-gate-report.template.md`
- Артефакты текущей стадии (пути из команды / чеклиста)
- При `stage-id` среза (`S-01` и др. из чеклиста) — `reports/checklist.md`

## Skill(s)

`.cursor/skills/skill-agent-anatomist.md`. Если `stage-id` = `qc-ft-nft` / `qc-us-uc` / `qc-ddd` — соответствующий точечный QC-скилл, без дублирования алгоритма. Срез `S-NN` и прочие команды из `list-commands.md` — универсальный чек-лист (см. скилл). Не путать сценарий S5 со срезом `S-05`.

## Output artifact(s)

`reports/review-report.md` (универсальный гейт). Точечные отчёты (`incompatibility-*.md`, `domain-model-review.md`) — только если вызван соответствующий QC.

## Review manifest

Вердикт `pass` / `fail`, таблица замечаний `critical` / `major` / `minor`.

## Gate checklist

- `stage-id` прочитан, не выдуман.
- Команда найдена в `list-commands.md` или это id среза чеклиста.
- Critical/major блокируют смену глобального этапа.
- Анатомист не пишет `APPROVED`. Если `stage-id` пришёл в запросе — можно обновить только строку `- stage-id:` в `pm-state.md`.

## Update traceability

Не обновляй `reports/traceability.md` сам, если ПМ не поручил. В отчёте перечисли, каких связей не хватает.

## Ввод

`$1` и дальнейший текст — уточнение: другой `stage-id`, путь отчёта, только чек-лист без точечного QC.

Если текста нет — бери `stage-id` из `reports/pm-state.md`.

## После выполнения

Кратко для ПМ: `stage-id`, команда, путь отчёта, вердикт, число critical/major/minor. Не утверждай этап.
