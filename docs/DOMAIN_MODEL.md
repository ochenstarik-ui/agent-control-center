# Domain Model — Agent Control Center

**Версия:** 0.1.0-draft
**Статус:** Draft
**Нормативность:** supporting; при конфликте приоритет у SPECIFICATION.md

## Сущности

### Organization
| Поле | Тип | Описание |
|---|---|---|
| id | UUID | Первичный ключ |
| name | string | Название организации |
| slug | string | Уникальный идентификатор для URL |
| billing_email | string | Email для биллинга |
| created_at | timestamptz | Дата создания |

**Связи:** 1 → N Workspace

### Workspace
| Поле | Тип | Описание |
|---|---|---|
| id | UUID | PK |
| organization_id | UUID | FK → Organization |
| name | string | Название рабочего пространства |
| owner_account_id | UUID | FK → Account (владелец) |
| ai_lockout | boolean | Блокировка AI-действий |
| created_at | timestamptz | |

**Связи:** 1 → N Project, 1 → N Member

### Project
| Поле | Тип | Описание |
|---|---|---|
| id | UUID | PK |
| workspace_id | UUID | FK → Workspace |
| name | string | |
| description | text | |
| status | enum | active, archived, deleted |
| created_at | timestamptz | |

**Связи:** 1 → N Task, 1 → N Artifact

### Task
| Поле | Тип | Описание |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | FK → Project |
| title | string | |
| description | text | |
| priority | enum | low, medium, high, critical |
| status | enum | backlog, todo, in_progress, review, done |
| assignee_id | UUID | FK → Account (опционально) |
| created_at | timestamptz | |

**Связи:** 1 → N Run

### Run
| Поле | Тип | Описание |
|---|---|---|
| id | UUID | PK |
| task_id | UUID | FK → Task |
| agent_id | UUID | FK → Agent |
| connector_id | UUID | FK → Connector |
| status | enum | см. State Machine |
| goal | text | Цель запуска |
| context_bundle | jsonb | Bounded context |
| started_at | timestamptz | |
| completed_at | timestamptz | |
| error_message | text | |

### Agent
| Поле | Тип | Описание |
|---|---|---|
| id | UUID | PK |
| connector_id | UUID | FK → Connector |
| name | string | |
| runtime | enum | hermes, openclaw, claude, codex, gemini, generic |
| model | string | Идентификатор модели |
| tools | jsonb | Доступные инструменты |
| capabilities | jsonb | FK → Capability Registry |
| config_ref | string | Ссылка на конфигурацию |

### Connector
| Поле | Тип | Описание |
|---|---|---|
| id | UUID | PK |
| name | string | |
| host | string | Адрес сервера |
| status | enum | online, offline, degraded |
| version | string | Версия коннектора |
| last_heartbeat | timestamptz | |
| capabilities | jsonb | |

### Artifact
| Поле | Тип | Описание |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | FK → Project |
| run_id | UUID | FK → Run (опционально) |
| name | string | |
| type | string | MIME-тип |
| size_bytes | bigint | |
| storage_key | string | Ключ в Object Storage |
| checksum | string | SHA-256 |
| created_at | timestamptz | |

### Memory
| Поле | Тип | Описание |
|---|---|---|
| id | UUID | PK |
| scope | string | user, project, workspace |
| scope_id | UUID | ID области видимости |
| key | string | Ключ записи |
| value | text | Содержимое |
| provenance | string | Источник (agent_id, user_id) |
| version | int | Версия записи |
| created_at | timestamptz | |

### Skill
| Поле | Тип | Описание |
|---|---|---|
| id | UUID | PK |
| name | string | Уникальное имя |
| version | string | Семантическая версия |
| content | text | SKILL.md |
| signature | text | Подпись (опционально) |
| review_status | enum | draft, reviewed, approved, deprecated |
| created_by | string | agent_id или user_id |
| created_at | timestamptz | |

### WikiPage
| Поле | Тип | Описание |
|---|---|---|
| id | UUID | PK |
| workspace_id | UUID | FK → Workspace |
| path | string | Путь страницы |
| title | string | |
| content | text | Markdown |
| version | int | |
| updated_at | timestamptz | |

### Approval
| Поле | Тип | Описание |
|---|---|---|
| id | UUID | PK |
| run_id | UUID | FK → Run |
| action | string | Описание действия |
| risk_level | enum | low, medium, high, critical |
| requested_by | UUID | Кто запросил |
| status | enum | pending, approved, denied, expired |
| decided_by | UUID | Кто принял решение |
| created_at | timestamptz | |
| decided_at | timestamptz | |

### AuditEvent
| Поле | Тип | Описание |
|---|---|---|
| id | UUID | PK |
| event_type | string | Тип события |
| actor_id | UUID | Кто совершил |
| target_type | string | Тип цели |
| target_id | UUID | ID цели |
| payload | jsonb | Детали события |
| created_at | timestamptz | |

### User / Account
| Поле | Тип | Описание |
|---|---|---|
| id | UUID | PK |
| email | string | Уникальный |
| display_name | string | |
| password_hash | string | |
| mfa_enabled | boolean | |
| created_at | timestamptz | |

### Role
| Поле | Тип | Описание |
|---|---|---|
| id | UUID | PK |
| name | string | owner, admin, lead, operator, contributor, viewer |
| permissions | jsonb | Список разрешений |

**Связи:** User N ↔ M Role (через user_roles)

## Индексы

```sql
-- Поиск задач по проекту и статусу
CREATE INDEX idx_task_project_status ON task(project_id, status);

-- Поиск запусков по агенту и статусу
CREATE INDEX idx_run_agent_status ON run(agent_id, status);

-- Поиск артефактов по проекту
CREATE INDEX idx_artifact_project ON artifact(project_id);

-- Аудит по времени
CREATE INDEX idx_audit_created ON audit_event(created_at DESC);

-- Поиск memory по scope
CREATE INDEX idx_memory_scope ON memory(scope, scope_id, key);
```
