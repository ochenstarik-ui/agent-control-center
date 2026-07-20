# State Machines — Agent Control Center

**Версия:** 0.1.0-draft | **Статус:** Draft

## Run State Machine

```
                    ┌─────────┐
                    │ QUEUED  │
                    └────┬────┘
                         │ dispatch
                    ┌────▼────┐
                    │ PENDING │
                    └────┬────┘
                         │ connector accepts
                    ┌────▼────┐
                    │ RUNNING │◄──────────────┐
                    └────┬────┘               │
          ┌──────────────┼──────────────┐     │
          ▼              ▼              ▼     │
    ┌──────────┐  ┌───────────┐  ┌──────────┐ │
    │COMPLETED │  │  FAILED   │  │CANCELLED │ │
    └──────────┘  └───────────┘  └──────────┘ │
                                               │
    ┌──────────┐                               │
    │  PAUSED  │───────────────────────────────┘
    └──────────┘        resume
```

**Переходы:**
| Из | В | Условие |
|---|---|---|
| QUEUED | PENDING | Scheduler dispatch |
| PENDING | RUNNING | Connector accept |
| PENDING | FAILED | Timeout / connector offline |
| RUNNING | COMPLETED | Agent finished successfully |
| RUNNING | FAILED | Error / timeout |
| RUNNING | CANCELLED | User cancel / policy |
| RUNNING | PAUSED | User pause / preemption |
| PAUSED | RUNNING | User resume |
| PAUSED | CANCELLED | User cancel while paused |

**Инварианты:**
- COMPLETED/FAILED/CANCELLED — терминальные, не могут переходить
- Только один Run активен на Agent одновременно (MUST)
- CANCELLED → terminal; cleanup resources within 30s (SHOULD)

## Task State Machine

```
    ┌─────────┐     ┌──────────┐     ┌───────────┐
    │ BACKLOG │────►│   TODO   │────►│ IN_PROGRESS│
    └─────────┘     └──────────┘     └─────┬─────┘
         ▲                                 │
         │                    ┌────────────┼────────────┐
         │                    ▼            ▼            ▼
         │              ┌─────────┐  ┌─────────┐  ┌──────┐
         └──────────────│  DONE   │  │ BLOCKED │  │ REVIEW│
                        └─────────┘  └─────────┘  └──┬───┘
                                                     │
                                                     ▼
                                               ┌─────────┐
                                               │  DONE   │
                                               └─────────┘
```

## Project State Machine

```
    ┌─────────┐     ┌────────┐     ┌──────────┐
    │  DRAFT  │────►│ ACTIVE │────►│ ARCHIVED │
    └─────────┘     └────────┘     └──────────┘
                         │               ▲
                         └───────────────┘
                            reactivate
```

## Connector State Machine

```
    ┌──────────┐     ┌────────┐     ┌───────────┐
    │REGISTERING│───►│ ONLINE │────►│ DEGRADED  │
    └──────────┘     └───┬────┘     └─────┬─────┘
                         │               │
                         ▼               ▼
                    ┌─────────┐    ┌──────────┐
                    │ OFFLINE │◄───│ OFFLINE  │
                    └─────────┘    └──────────┘
```

**Переходы:**
| Событие | Переход |
|---|---|
| Heartbeat OK (каждые 30s) | → ONLINE |
| Heartbeat missed × 3 | ONLINE → DEGRADED |
| Heartbeat missed × 10 | DEGRADED → OFFLINE |
| Reconnect | OFFLINE → ONLINE |

## Approval State Machine

```
    ┌─────────┐     ┌───────────┐
    │ PENDING │────►│ APPROVED  │
    └────┬────┘     └───────────┘
         │
         ├──────────►┌──────────┐
         │           │  DENIED  │
         │           └──────────┘
         │
         └──────────►┌──────────┐
                     │ EXPIRED  │ (timeout 5 min)
                     └──────────┘
```

**Правила:**
- PENDING → APPROVED/DENIED: только authorized approver (не self-approval для high/critical)
- PENDING → EXPIRED: автоматически через 5 минут
- EXPIRE → новый Approval (MUST)
