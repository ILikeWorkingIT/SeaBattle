# Список команд

Актуальный список команд запуска скиллов и агентов. Обновлять при создании нового скилла, агента или команды.

| Команда | Файл | Назначение |
| --- | --- | --- |
| `/pin-memory` | `.cursor/commands/pin-memory.md` | Быстро сохранить устойчивый вывод из чата в `reports/agent-memory.md` |
| `/ft` | `.cursor/commands/ft.md` | Написать или обновить функциональные требования по `.cursor/skills/skill-ft.md` |
| `/nft` | `.cursor/commands/nft.md` | Написать или обновить нефункциональные требования по `.cursor/skills/skill-nft.md` |
| `/us` | `.cursor/commands/us.md` | Написать или обновить User Stories, роли и права по `.cursor/skills/skill-us.md` |
| `/uc` | `.cursor/commands/uc.md` | Написать или обновить Use Cases (Cockburn) по `.cursor/skills/skill-uc.md` |
| `/qc-ft-nft` | `.cursor/commands/qc-ft-nft.md` | Проверить качество ФТ и НФТ по `.cursor/skills/skill-quality-control-ft-nft.md` |
| `/qc-us-uc` | `.cursor/commands/qc-us-uc.md` | Проверить качество US и UC по `.cursor/skills/skill-quality-control-us-uc.md` |
| `/diagram-bpmn` | `.cursor/commands/diagram-bpmn.md` | Моделировать бизнес-процесс в BPMN 2.0 для bpmn.io по `.cursor/skills/skill-diagram-bpmn.md` |
| `/diagram-mermaid` | `.cursor/commands/diagram-mermaid.md` | Mermaid: flowchart, DFD, classDiagram, sequenceDiagram, C4 по `.cursor/skills/skill-diagram-mermaid.md` |
| `/ddd` | `.cursor/commands/ddd.md` | Доменная модель (DDD) по `.cursor/skills/skill-ddd.md`; в конце обязательно ревью `.cursor/skills/skill-review-ddd.md` |
| `/review-ddd` | `.cursor/commands/review-ddd.md` | Критический аудит DDD-модели по `.cursor/skills/skill-review-ddd.md` (самостоятельный режим: только отчёт) |
| `/data-dictionary` | `.cursor/commands/data-dictionary.md` | Словарь данных (поля, типы, ограничения, MVP) по `.cursor/skills/skill-data-dictionary.md`; после записи файла обязателен гейт проверки до отчёта |
| `/ui-prototyping` | `.cursor/commands/ui-prototyping.md` | Интерактивный макет окна фронтенда по `.cursor/skills/skill-ui-prototyping.md` |
| `/openai` | `.cursor/commands/openai.md` | OpenAPI-спецификация (YAML, Swagger UI + ReDoc) по `.cursor/skills/skill-openai.md`; после записи файла обязателен гейт проверки и просмотрщики |

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

## Режимы `/ui-prototyping`

Отдельной подкоманды нет: режим выбирается по содержимому запроса. Это одна команда, не три.

**Создание** — «сделай макет», клиента ещё нет. Агент пишет UI и mock. В конце чата: где код, какой экран, как открыть окно или URL **самим** (не из терминала агента в чате).

**Правка** — макет уже есть, точечная просьба («текст жёлтый», баг кнопки). Агент меняет только это и напоминает перезапустить тем же способом. Новый макет и README с нуля не делает.

**Только запуск** — «не вижу окно», «как открыть». Код не трогает. В чате только способ: launcher в проводнике и/или URL в своём браузере.

