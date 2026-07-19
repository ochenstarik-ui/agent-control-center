# Открытые решения

**Версия:** 0.1.0-draft
**Правило:** вопросы с severity `BLOCKER` должны быть закрыты ADR/approval до реализации затрагиваемой части.

| ID | Severity | Решение | Варианты / критерии | Владелец | Deadline | Статус |
|---|---|---|---|---|---|---|
| OQ-001 | BLOCKER | Модель продукта и deployment | single-tenant self-hosted first vs multi-tenant hosted; data residency, ops cost | Product/Architecture | До M0 exit | Open |
| OQ-002 | BLOCKER | Client stack | React+Tauri+Capacitor baseline vs Flutter/другое; security, parity, terminal/editor UX, team skills | Architecture | До M0 exit | Open |
| OQ-003 | BLOCKER | Auth baseline | local bootstrap + OIDC; enterprise SSO/SCIM phase; recovery and break-glass | Security/Product | До M1 | Open |
| OQ-004 | BLOCKER | Supported OS/Android API matrix | реальные устройства, distribution channels, update/signing ownership | Product/Release | До M0 exit | Open |
| OQ-005 | BLOCKER | Adapter MVP matrix | обязательны Hermes/OpenClaw; выбрать Claude/Codex/Gemini spike и exact pinned versions | Product/Integration | До M0 exit | Open |
| OQ-006 | BLOCKER | Connector sandbox | container/systemd users/Windows job objects/macOS sandbox; filesystem/network policies | Security/Architecture | До M2 | Open |
| OQ-007 | BLOCKER | Data classification/retention | classes, regions, default retention, legal hold/privacy delete | Security/Legal | До M1 | Open |
| OQ-008 | BLOCKER | Persistence/queue/vector stack | managed vs self-hosted; extensions, backup, data residency, rebuild | Architecture/Operations | До M1 | Open |
| OQ-009 | BLOCKER | Approval/risk policy | destructive definitions, dual-control, self-approval, in-flight budget action | Security/Product | До M1 | Open |
| OQ-010 | BLOCKER | License/business model | repository/product license, third-party redistribution, SDK/CLI terms | Owner/Legal | До external distribution | Open |
| OQ-011 | MAJOR | Offline mobile policy | exact safe mutation allowlist, cache sensitivity, retention and remote wipe | Product/Security | До M5 | Open |
| OQ-012 | MAJOR | Usage/cost normalization | currencies/units, authoritative providers, manual budgets, exchange rates | Product/Finance | До M3 | Open |
| OQ-013 | MAJOR | Memory embeddings | provider, local/remote, sensitivity, re-embedding version policy | Architecture/Security | До M4 | Open |
| OQ-014 | MAJOR | Skill signing/review | organization signing keys, scanner set, approval roles, revocation distribution | Security | До M4 | Open |
| OQ-015 | MAJOR | Handoff bundle limits | token/byte limits, summary algorithm, human preview UX, language handling | Product/Integration | До M3 | Open |
| OQ-016 | MAJOR | SLO ownership and pilot size | production profile, on-call, telemetry, capacity and pilot tenants | Operations/Product | До M6 | Open |
| OQ-017 | MINOR | Branding/localization | product name validation, Russian/English MVP, terminology | Product/Design | До UX freeze | Open |
| OQ-018 | MINOR | Notifications | FCM/email providers, privacy-safe previews, quiet hours | Product/Operations | До M5 | Open |

## Decision template

```markdown
# ADR-NNN: Title
Status: proposed | accepted | superseded
Date:
Owners:
Related: OQ-..., FR-..., NFR-...

## Context
## Options and evidence
## Decision
## Security/privacy/operational consequences
## Migration and rollback
## Validation
```
