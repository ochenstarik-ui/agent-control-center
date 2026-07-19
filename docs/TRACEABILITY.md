# Traceability matrix

**Версия:** 0.1.0-draft
**Статус значений:** `Specified` означает «описано и имеет acceptance contract», а не «реализовано».

## Пользовательский запрос → нормативные требования

| Верхнеуровневый запрос | Нормативные требования | Архитектурный артефакт | Acceptance evidence | Статус |
|---|---|---|---|---|
| Единое рабочее пространство | FR-PRJ-001..006, FR-RUN-001..009, NFR-UX-001..003 | `ARCHITECTURE.md` §1–3 | E2E-002, E2E-007 | Specified |
| Проекты и задачи | FR-PRJ-001..006 | canonical entities + Project Service | AT-FR-PRJ-001..006 | Specified |
| Управление серверными ИИ-агентами | FR-CON-001..007, FR-RUN-001..009 | outbound Connector + AAP | E2E-001, E2E-002, E2E-006 | Specified |
| Hermes | FR-CON-003..006, AAP contract | Hermes native HTTP adapter; `RESEARCH.md` | pinned adapter contract suite (M2) | Specified; spike pending |
| OpenClaw | FR-CON-003..006, AAP contract | OpenClaw Gateway adapter; `RESEARCH.md` | pinned adapter contract suite (M2) | Specified; spike pending |
| Claude Code | FR-CON-003..006, AAP contract | Agent SDK adapter; `RESEARCH.md` | adapter spike/contract suite | Specified; OQ-005 open |
| OpenAI Codex | FR-CON-003..006, AAP contract | app-server/SDK adapter; `RESEARCH.md` | adapter spike/contract suite | Specified; OQ-005 open |
| ChatGPT/OpenAI | FR-CON-003..006, FR-RUN-001..009 | Responses/Conversations API adapter; consumer ChatGPT UI excluded | API adapter contract suite | Specified; boundary explicit |
| Gemini | FR-CON-003..006, AAP contract | headless structured adapter; `RESEARCH.md` | adapter spike/contract suite | Specified; OQ-005 open |
| Web-клиент | NFR-UX-001..003, NFR-PORT-001/004 | shared React UI/PWA baseline | E2E-007 + browser matrix | Specified; ADR-001 open |
| Desktop-клиент | NFR-UX-001..003, NFR-PORT-002/004 | Tauri wrapper baseline | E2E-007 + OS install/upgrade matrix | Specified; ADR-001/OQ-004 open |
| Android-клиент | NFR-UX-001..003, NFR-PORT-003/004 | Capacitor wrapper baseline | E2E-007 + device/offline matrix | Specified; ADR-001/OQ-004 open |
| Переключение при исчерпании лимитов | FR-RUN-006..009, FR-OPS-001..002, NFR-REL-004 | checkpoint/handoff state machine + Usage Service | E2E-003; fault/boundary tests | Specified |
| Общая память проекта | FR-MEM-001..007, NFR-SEC-004/005/007 | Context Broker + Memory Service | E2E-004; leakage/conflict/rebuild tests | Specified |
| База skills | FR-SKL-001..005, NFR-SEC-005/008 | Skill Registry + quarantine/review/pinning | E2E-005 | Specified |
| Wiki | FR-WIK-001..004 | Wiki Service + revision/citation model | E2E-004 + AT-FR-WIK-* | Specified |
| Безопасность, approvals, audit | FR-IAM-001..005, FR-OPS-004..005, NFR-SEC-001..008 | Identity/Policy/Audit + threat model | E2E-008 + security gates | Specified |
| Архитектура и модель данных | SPEC §9–11; ARCH §1–8 | `ARCHITECTURE.md` | structural G1 + later migration/contract tests | Specified |
| API и события | SPEC §9; FR-CON/RUN | REST/WSS/AAP baseline | adapter/API contract tests | Specified |
| Acceptance-тесты | каждый FR/NFR связан с одноимённым AT | SPEC §12 | `scripts/validate_spec.py`, QA evidence in implementation phase | Specified |

## Артефакты → назначение

| Файл | Назначение | Gate |
|---|---|---|
| `README.md` | входная точка, статус и запрет реализации | G1 |
| `docs/SPECIFICATION.md` | канонические требования и acceptance contract | G1 |
| `docs/ARCHITECTURE.md` | component/data/API/AAP baseline и trust boundaries | G1/ADR |
| `docs/RESEARCH.md` | source-backed integration constraints | G1 + implementation spikes |
| `docs/OPEN-QUESTIONS.md` | blocking decisions и owners | G0 |
| `docs/TRACEABILITY.md` | запрос → requirement → evidence mapping | G1 |
| `scripts/validate_spec.py` | machine-checkable structural invariants | G1/CI |
| `tests/test_validate_spec.py` | regression tests validator/trace mapping | G1/CI |

## Реализация

На момент этой версии отсутствует. Ни одна строка `Specified` не должна интерпретироваться как готовая функция. Переход к реализации разрешён только после G0/G1 и явного operator approval.
