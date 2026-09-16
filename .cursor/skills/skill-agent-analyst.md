---
name: skill-agent-analyst
description: >-
  Router for the analyst agent. Opens existing /ft /us /uc /diagram-* skills.
  Does not open /vision (tech-writer). Does not duplicate their algorithms.
disable-model-invocation: true
owner: analyst
---

# Скилл агента analyst

Открой и выполни точечный скилл. Этот файл — только маршрутизатор.

| Задача | Команда | Скилл |
| --- | --- | --- |
| Функциональные требования | `/ft` | `.cursor/skills/skill-ft.md` |
| User Stories | `/us` | `.cursor/skills/skill-us.md` |
| Use Cases | `/uc` | `.cursor/skills/skill-uc.md` |
| BPMN | `/diagram-bpmn` | `.cursor/skills/skill-diagram-bpmn.md` |
| Mermaid | `/diagram-mermaid` | `.cursor/skills/skill-diagram-mermaid.md` |

НФТ и DDD — не эта роль. Vision & Scope — `/vision` (роль `tech-writer`, `skill-vision`). После написания предложи точечный QC, не запускай его без согласия.
