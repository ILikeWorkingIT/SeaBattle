# Состояние ПМ

Создано из `reports/templates/pm-state.template.md` для репозитория Sea Battle.

## Текущий этап

- stage-id:
- stage-name:
- status: idle
- approval:
- исполнитель:
- очередь:

`status`: `idle` | `in-progress` | `gate` | `blocked` | `awaiting-approval`.
`approval`: пусто или `Stage: <stage-id>: APPROVED`. ПМ пишет эту строку только после фразы пользователя «утверждаю» / «принимаю этап».

## Гейт качества

- последний `/qc-stage`:
- вердикт:
- critical / major открыты:
- minor / known issues:

## Контекст репозитория (не срез чеклиста)

- Сценарий MAS: S3 (требования, US/UC, DDD, словарь, OpenAPI, макет PySide6 уже есть).
- `reports/checklist.md` срезов кода нет — не выдумывать S-01…S-13.
- Бэкенд `src/backend/` ещё не создан; клиентский макет — `src/frontend/`.
- Следующий осмысленный шаг после `/pm` (статус): согласовать, нужен ли `/app-layer` (каркас FastAPI+Redis) или точечная правка документов / макета.

## Блокеры

-

## Очередь действий

-
