# Roadmap — Agent Control Center

**Версия:** 0.1.0-draft | **Статус:** Draft

## Фазы

### M0 — Foundations (4 недели)
**Цель:** спецификация утверждена, репозиторий готов к реализации.

| Задача | Статус |
|---|---|
| Закрыть блокирующие OQ-001..OQ-005 | ⏳ |
| Утвердить SPECIFICATION.md (G1 PASS) | ⏳ |
| Утвердить Domain Model | ⏳ |
| Утвердить State Machines | ⏳ |
| Настроить CI + линтеры | ⏳ |
| Развернуть dev-окружение | ⏳ |

### M1 — Core (8 недель)
**Цель:** минимальный Control Plane: workspace, project, task, agent registry.

| Компонент | Что входит |
|---|---|
| Identity & Policy | OIDC, local bootstrap admin |
| Project Service | CRUD projects, tasks |
| Connector Gateway | WSS, register, heartbeat |
| Agent Registry | Adapters: Hermes, OpenClaw |
| Run Orchestrator | create_run, stream_events, cancel |
| Approval Service | Basic approve/deny для destructive actions |
| Audit Service | Immutable audit log |

### M2 — Context (6 недель)
**Цель:** общий контекст между агентами.

| Компонент | Что входит |
|---|---|
| Context Broker | Bounded context bundle, redaction |
| Memory Service | Scoped memory, versions, search |
| Skill Registry | Skill upload, versioning, signing |
| Wiki Service | Markdown pages, links, search |
| Handoff | Полный handoff contract |
| Artifact Storage | Upload/download, checksums |

### M3 — Operations (6 недель)
**Цель:** observability, quotas, мониторинг.

| Компонент | Что входит |
|---|---|
| Usage Service | Quota tracking, budget alerts |
| Scheduler | Priority + Fair Queue |
| Event Bus | Durable delivery, replay |
| Monitoring | Health dashboard, SLO метрики |
| Backup/Restore | Git-based config backup |
| Error Catalog | Единые коды ошибок |

### M4 — Clients (8 недель)
**Цель:** три клиента с общим UI-ядром.

| Клиент | Платформа |
|---|---|
| Web / PWA | React + TypeScript |
| Desktop | Tauri (Windows, macOS, Linux) |
| Android | Capacitor wrapper |

**Функциональность клиентов:**
- Workspace/project/task management
- Agent dashboard + live run monitor
- Approval UI (push notifications)
- Memory/Wiki browser
- Skill browser + install
- Kanban board

### M5 — Enterprise (8 недель)
**Цель:** production-ready для нескольких tenants.

| Компонент | Что входит |
|---|---|
| Multi-tenancy | Организации, SSO/SAML |
| Connector sandbox | Container-based (Docker/podman) |
| Advanced approval | Dual-control, custom policies |
| Notifications | Email, FCM, webhook |
| SLA monitoring | SLO панель, инциденты |
| Capacity | 50 users, 20 connectors, 100 concurrent runs |

## Временная шкала

```
M0 ──── M1 ──────── M2 ────── M3 ────── M4 ──────── M5 ──────
│       │           │         │         │           │         │
0       4          12        18        24          32        40 недель
```

## Зависимости между фазами

```
M0 (Spec) ──► M1 (Core) ──► M2 (Context) ──► M3 (Ops)
                        │                      │
                        └──────► M4 (Clients) ◄┘
                                    │
                                    └──► M5 (Enterprise)
```

## Критерии готовности MVP (M1+M2)

- [ ] 1 workspace, 1 project, 3 агента (Hermes) — create/run/monitor
- [ ] Handoff между 2 агентами — контекст не потерян
- [ ] Approval для destructive action — работает через UI
- [ ] Memory/Wiki — запись и поиск
- [ ] Web-клиент — полный цикл управления
- [ ] 5 последовательных ручных прогонов без ошибок
