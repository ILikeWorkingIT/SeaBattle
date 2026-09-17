# Ключи Redis (вместо ER)

**Тип:** flowchart связей ключей  
**Срез:** инфраструктура as-is `redis_session_store.py`, `redis_ledger_store.py`.  
**Статус:** черновик витрины.

SQL/ER нет. Heatmap ключа не имеет.

---

```mermaid
flowchart LR
  subgraph registry["SET"]
    slots["seabattle:registry:slots"]
  end
  subgraph session["STRING plus EX"]
    sess["seabattle:session:id"]
  end
  subgraph ledger["журнал"]
    counters["HASH counters"]
    records["LIST records"]
    recorded["SET recorded sessionId"]
  end
  slots -->|"id активных до 3"| sess
  sess -->|"GAME_OVER Lua"| recorded
  recorded --> records
  recorded --> counters
```

Lua старта: SCARD слотов < 3, SADD, SET JSON EX. Lua исхода: SISMEMBER recorded, иначе LPUSH + HINCRBY.
