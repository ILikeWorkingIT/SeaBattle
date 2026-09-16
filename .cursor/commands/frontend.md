---
description: >-
  Рабочий desktop UI (PySide6, тема, стейт, objectName) по
  skill-frontend-developer. Макет без логики — /ui-prototyping.
---

# Рабочий UI приложения

Прочитай и выполни `.cursor/skills/skill-frontend-developer.md` целиком. Команда `/frontend` запускает этот скилл.

Это **рабочий** desktop UI (PySide6): виджеты, тема, стейт, loading/error/empty по канону. Это **не** макет «клики без функционала» — для макета нужна `/ui-prototyping`.

Не пиши React, браузер, Gradio, Streamlit. HTML `data-testid` не ставь: на интерактивном виджете — `self.<роль>` и `setObjectName`. Подписи глоссария не переименовывай.

Не выполняй `.cursor/skills/skill-new-tests.md` и `.cursor/skills/skill-use-tests.md` в этом запуске. После правки предложи `/new-tests` и `/use-tests` отдельными командами.

Не запускай окно из терминала агента. Напомни `src/run-frontend.bat`.

## Режим

По запросу выбери **один**:

- **фича** — экран / кнопка / стейт по ФТ, US, UC, `Axxxx`;
- **баг** — регрессия интерфейса, гонка, блокировка;
- **полировка** — вид без смены правил ФТ; селекторы QA не ломай.

`$1` и дальнейший текст — какой экран; какие ID; баг или полировка.

Если просят только макет — **остановись**. Нужна `/ui-prototyping`. FastAPI / Redis / heatmap — `/app-layer`. Только тесты — `/new-tests`. Только прогон — `/use-tests`.

## После выполнения

Кратко: режим; какие виджеты / `objectName` / токены; как открыть окно самим; предложи `/use-tests` (и `/new-tests` при новых контролах). В этом запуске их не выполняй.
