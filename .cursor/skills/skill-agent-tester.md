---
name: skill-agent-tester
description: >-
  Router for the tester agent. Opens skill-new-tests or skill-use-tests.
  Does not change product code.
disable-model-invocation: true
owner: tester
---

# Скилл агента tester

| Задача | Команда | Скилл |
| --- | --- | --- |
| Написать / дополнить тесты | `/new-tests` | `.cursor/skills/skill-new-tests.md` |
| Прогон и очередь багов | `/use-tests` | `.cursor/skills/skill-use-tests.md` |

Продуктовый код в `src/` не меняй. Не гоняй набор в том же ходе, что `/new-tests`.
