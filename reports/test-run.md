# Прогон автотестов

- Дата-время: 2026-09-17 11:08:02 (UTC+5)
- Команда: `python -m pytest --tb=short` (корень: `E:\Cursor\SeaBattle`, `pytest.ini`, `testpaths = tests`)
- OS: win32 (Windows 10), Python 3.12.0, pytest-9.1.1, pluggy-1.6.0, asyncio-1.4.0, anyio-4.11.0
- Итог: collected 279; 279 passed, 0 failed, 0 error, 0 skipped; 1 warning; 4.67s
- Режим: прогон
- Вердикт: PASS
- Предупреждение: StarletteDeprecationWarning — `httpx` + `starlette.testclient` (пакет FastAPI), на вердикт не влияет
- Примечание: повторный полный прогон после фикса оракула BUG-001. Код продукта не менялся. Новые тесты не писались. GUI не открывался. Watch не использовался. Kill по таймауту не применялся. Прогонов полного набора: 2/4 этого запуска скилла.

## Очередь дефектов

| ID | Тест | Файл теста | Тип | Воспроизведение | Ожидание | Факт | Требования | Где чинить | Доказательство | Статус |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BUG-001 | `test_should_show_surrender_error_when_ws_rejects` | `tests/test_should_show_surrender_when_player_confirms.py` | `test_defect` | `python -m pytest tests/test_should_show_surrender_when_player_confirms.py::test_should_show_surrender_error_when_ws_rejects --tb=short` | После фикса оракула: подпись ошибки сдачи = `window.i18n.t("err_validation")` (канон OpenAPI / i18n) при `code=VALIDATION_ERROR`; фаза `error`, экран партии, матч не завершён. | Тест зелёный в полном наборе. Продукт мапит `VALIDATION_ERROR` в ключ i18n (`MainWindow._localize_tagged`). | UC-005 §5.1; OpenAPI `VALIDATION_ERROR` `messageRu`; FT-059 / FT-061 | Тест (оракул). Продукт не трогать. | Предыдущий прогон (1/4): `AssertionError: assert 'В запросе нет обязательных полей или неверный тип данных.' == 'неверная полезная нагрузка'`. Этот прогон (2/4): 279 passed, файл теста в наборе зелёный. | исправлен |

Доказательство (этот прогон):

    FAILED нет. tests/test_should_show_surrender_when_player_confirms.py — все кейсы прошли.
    279 passed, 1 warning in 4.67s
