---
name: skill-agent-tech-writer
description: >-
  Router for the tech-writer agent. Opens /vision (skill-vision) and /gost-3460289
  (skill-gost-3460289). Slice A has no /report-weekly yet; other drafts only from
  existing report facts.
disable-model-invocation: true
owner: tech-writer
---

# Скилл агента tech-writer

Открой и выполни точечный скилл. Этот файл — только маршрутизатор.

| Задача | Команда | Скилл |
| --- | --- | --- |
| Vision & Scope | `/vision` | `.cursor/skills/skill-vision.md` |
| ТЗ по ГОСТ 34.602-89 | `/gost-3460289` | `.cursor/skills/skill-gost-3460289.md` |

Команды `/report-weekly`, `/report-presentation`, `/release-notes` файлами не созданы.

Если ПМ просит текст для заказчика (не Vision):

1. Читай только существующие файлы в `reports/` (в том числе `daily/`, `commit-audit/`, `test-run.md`, `checklist.md`).
2. Пустые папки не заполняй выдуманными событиями. Напиши, каких артефактов не хватает.
3. Не меняй таблицы требований в `requirements/` и код в `src/`. Для `/vision` допускается запись `artifacts/vision-scope.md` и закрытых пар `VS` в `answers-project.md` по скиллу. Для `/gost-3460289` — запись `artifacts/tz-gost-<код>.md` и закрытых пар `TZ` в `answers-project.md` по скиллу.
