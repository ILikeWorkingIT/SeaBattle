# ADR-005: heatmap не на клиенте

**Статус:** принято (FT-050, A0014, A0095).  
**Дата фиксации в витрине:** 2026-09-17.

## Контекст

Ход Бэкенда считается матрицей вероятностей Hunt/Target. Показ весов сломал бы скрытие флота и превратился бы в подсказку.

## Решение

`compute_aim` только в domain/application на сервере. VO heatmap в Redis и в JSON API нет. Игрок видит клетку и `MISS`/`HIT`/`SUNK`. UI режимы Hunt/Target не рисует.

## Следствия

Обзор ИИ для слайда: [diagram-ai-overview.md](../../../diagrams/diagram-ai-overview.md). Канон ветвлений: `diagram-mermaid-001.md`.
