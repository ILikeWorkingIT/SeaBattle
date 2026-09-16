---
name: skill-agent-architect
description: >-
  Router for the architect agent. Opens existing /nft /ddd /data-dictionary
  /openai skills. Does not duplicate their algorithms.
disable-model-invocation: true
owner: architect
---

# Скилл агента architect

Открой и выполни точечный скилл.

| Задача | Команда | Скилл |
| --- | --- | --- |
| Нефункциональные требования | `/nft` | `.cursor/skills/skill-nft.md` |
| Доменная модель | `/ddd` | `.cursor/skills/skill-ddd.md` |
| Словарь данных | `/data-dictionary` | `.cursor/skills/skill-data-dictionary.md` |
| OpenAPI | `/openai` | `.cursor/skills/skill-openai.md` |

В этом репозитории свой HTTP API есть (`reports/project-config.md`, `requirements/openapi.yaml`). Не отказывайся обновлять контракт. Если в другом проекте API нет — тогда `openapi.yaml` не создавай.
