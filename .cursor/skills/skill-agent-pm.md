---
name: skill-agent-pm
description: >-
  Orchestration playbook for the PM agent. Use when acting as pm: set stage-id,
  route to existing slash commands, call /qc-stage, record user approval.
  Does not implement product code.
disable-model-invocation: true
owner: pm
---

# Скилл агента PM

Не копируй точечные скиллы. Маршрутизируй. Точка входа — `/pm`.

## Когда применять

Команда `/pm`, активен агент `pm`, или пользователь просит оркестрацию этапа / среза.

## Старт `/pm`

1. Если нет `reports/project-config.md` — создай по `reports/templates/project-config.template.md` из фактов `documentation/` и корня репозитория. Файл уже есть — не затирай уникальные поля.
2. Если нет `reports/pm-state.md` — создай по `reports/templates/pm-state.template.md`.
3. Прочитай `reports/navigator.md`, `.cursor/list-commands.md`. Если есть `reports/checklist.md` — найди **первый** срез без «Срез готов» (`[x]`). Не считай готовым срез только потому, что он раньше по номеру.
4. Дальше — по режиму команды `/pm` (статус / старт этапа / утверждение). Пустой `/pm` = статус, не конвейер всех ролей.

## Шаги оркестрации этапа

1. Зафиксируй `stage-id` в `pm-state.md`: имя команды без `/` (`ft`, `app-layer`, `qc-ft-nft`) или id среза из чеклиста (`S-05`).
2. Назначь исполнителя по таблице в `.cursor/agents/agent-pm.md`. В задаче укажи команду и путь скилла. Логику скилла не пересказывай целиком.
3. Срез с двумя слоями: сначала `/app-layer` (сервер / Redis / API), затем отдельным ходом `/frontend` (PySide6). В одном ответе оба слоя не меняй.
4. После артефакта вызови `/qc-stage` (агент anatomist, `skill-agent-anatomist`). Не в том же ходе, что написание кода, если пользователь не просил гейт уже готового пакета.
5. Critical/major — верни того же исполнителя. `stage-id` не меняй на следующий глобальный этап.
6. Гейт `pass` — статус `awaiting-approval`. Попроси «утверждаю» / «принимаю этап».
7. Только после этой фразы запиши `Stage: <stage-id>: APPROVED` в `pm-state.md`. Сам не утверждай.

## Запрещено

- Писать `src/` и подменять `/frontend` / `/app-layer`.
- Запускать тесты в том же ходе, что код среза.
- Ставить APPROVED без фразы пользователя.
- Запускать GUI из терминала агента.
