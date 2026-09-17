# Class: агрегат Session (слайд)

**Тип:** classDiagram  
**Срез:** одна схема корня Session. Полная модель: [diagram-class-001.md](diagram-class-001.md) (A0148).  
**Статус:** черновик витрины.

## Источники

Доменная модель, §7.1 канонической class-диаграммы. Службы `StartSession` и heatmap на слайд не вынесены.

---

```mermaid
classDiagram
  direction TB
  class Session {
    <<Entity>>
    +id GameSessionId
    +status Active_or_GameOver
    +turn Player_or_Backend
    +idleTtl 1800s
    +applyShot()
    +surrender()
  }
  class Board {
    <<Entity>>
    +owner Side
    +cells 10x10
  }
  class Fleet {
    <<Entity>>
    +owner Side
    +ships 10
  }
  class Ship {
    <<Entity>>
    +type length status
  }
  class Shot {
    <<Entity>>
    +seq shooter result
  }
  Session "1" *-- "2" Board : player and backend
  Session "1" *-- "2" Fleet : player and backend
  Session "1" *-- "0..*" Shot
  Fleet "1" *-- "10" Ship
```

Игроку на API отдаётся только `playerFleet`. Связи Registry / Ledger — на канонической схеме 7.2.

**Проверено:** латиница id классов; UI не классами.
