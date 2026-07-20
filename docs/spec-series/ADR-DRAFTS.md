# Черновики ADR по критичным пунктам из IMPROVEMENT-PROPOSALS.md

**Статус:** proposed (не accepted). Формат — из `docs/OPEN-QUESTIONS.md` (Decision template). Каждый ADR ссылается на конкретный пункт `IMPROVEMENT-PROPOSALS.md` и, если принят, должен быть перенесён в `docs/adr/` с финальным номером, а также отражён в `docs/OPEN-QUESTIONS.md` и `docs/TRACEABILITY.md`.

Отбор: сюда вынесены только пункты, которые (а) влияют на trust boundary/security invariants, либо (б) блокируют другие решения, либо (в) дешевле закрыть на уровне ADR сейчас, чем переделывать после M1.

---

## ADR-101: Emergency stop (workspace/tenant-wide kill switch)

```
Status: proposed
Date: 2026-07-20
Owners: Security, Architecture
Related: A1 (IMPROVEMENT-PROPOSALS.md), FR-RUN-005, NFR-REL-004, §11 State invariants
```

### Context
FR-RUN-005 определяет cancel только на уровне одного Attempt. При compromised skill, runaway agent или инциденте безопасности нет способа мгновенно остановить **все** active runs в workspace/tenant. Это блокирует раздел рисков E ("Runaway cost") и создаёт разрыв между заявленным Emergency access у Organization Owner (§2 SPECIFICATION) и реальной механикой.

### Options and evidence
1. **Broadcast cancel** — Control Plane итерирует все active Attempt в scope и шлёт обычный cancel каждому. Просто, но не atomic: часть runs может успеть создать side effect до получения команды; нет единого "замка" против нового dispatch.
2. **Scope-level dispatch lock + broadcast cancel** — перед broadcast'ом сначала атомарно переводится workspace/tenant в `dispatch_locked`, что немедленно блокирует любой новый `start`/`resume`/`handoff`-dispatch на уровне Run Orchestrator, затем существующие Attempt получают priority cancel с укороченным grace period.
3. **Connector-level circuit breaker** — Emergency stop транслируется в команду самому Connector "отклоняй все новые native calls", независимо от Control Plane state — сильнее защищает от split-brain (Control Plane недоступен), но требует доверенного канала Control Plane → Connector даже в degraded state.

### Decision (draft)
Рекомендуется комбинация 2+3: dispatch-lock на Control Plane для немедленной остановки нового dispatch + отдельная asynchronous команда Connector на circuit-breaker уровень, чтобы emergency stop работал даже при частичной недоступности Control Plane. Финальный выбор — за Architecture с учётом ADR-005 (Connector sandbox).

### Security/privacy/operational consequences
- Требует нового state `dispatch_locked` на уровне workspace/tenant, отдельного от run-level state machine (§11 инвариантов не меняет, но добавляет).
- Emergency stop должен сам быть доступен ограниченному набору ролей (Org Owner, возможно Workspace Admin) и логироваться как security event высшего severity — пересекается с ADR-102 (break-glass).
- Ложное срабатывание (случайный emergency stop) само по себе operational risk — нужен confirmation step, но не настолько тяжёлый, чтобы блокировать реальный инцидент.

### Migration and rollback
Аддитивно: новое requirement (**FR-SAF-001**), не меняет существующие FR-RUN-*. Rollback — просто не активировать функцию до готовности Connector circuit-breaker команды.

### Validation
Требуется новый acceptance test: N параллельных runs в workspace останавливаются за bounded time (например ≤10с for dispatch-lock, отдельный SLA для полного cancel всех Attempt), без "zombie" writer lease (перепроверка NFR-REL-004).

---

## ADR-102: Break-glass emergency access

```
Status: proposed
Date: 2026-07-20
Owners: Security, Product
Related: H1 (IMPROVEMENT-PROPOSALS.md), FR-IAM-003/004, §2 роль Organization Owner
```

### Context
"Emergency access" заявлена как задача Organization Owner в таблице ролей §2, но нет FR, описывающего механику: обходит ли она обычный RBAC/ABAC-чек, есть ли TTL, обязателен ли post-use review. Сейчас это единственная роль-привилегия в спецификации без acceptance test.

### Options and evidence
1. **Отдельный "break-glass" режим с explicit активацией** — Owner явно инициирует, система выдаёт time-boxed elevated token (например 30–60 минут), каждое действие в этом окне помечается `via_break_glass=true` в audit с severity=critical, окно нельзя продлить без повторной явной активации.
2. **Постоянно доступный "super-admin" bypass** — проще реализовать, но противоречит уже принятому в спецификации принципу (FR-IAM-003: каждая операция проходит RBAC+ABAC) и создаёт постоянный high-value target.
3. **Break-glass только через отдельный break-glass credential (не текущая сессия Owner)** — сильнее изолирует (компрометация обычной сессии Owner не даёт break-glass), но добавляет operational overhead (где хранится break-glass credential, как ротируется).

### Decision (draft)
Рекомендуется вариант 1 как MVP-baseline, с явной пометкой, что вариант 3 (отдельный credential) рассматривается post-MVP по мере роста compliance требований (пересекается с OQ-019 compliance scope).

### Security/privacy/operational consequences
- Every break-glass activation генерирует немедленный alert (не только audit-запись) ответственным ролям — иначе "emergency access" не будет обнаружен вовремя при злоупотреблении.
- Обязательный post-use review другим Admin/Owner (dual control post-factum, раз нельзя dual-control в моменте инцидента) — открытая запись до review блокирует, например, следующий billing cycle report или явно видна как "unreviewed break-glass" в security dashboard.
- Неиспользуемое право break-glass не должно молча "протухать" без напоминания — иначе Owner забывает, что оно вообще есть.

### Migration and rollback
Новое **FR-IAM-006**; не меняет существующие IAM-инварианты, но требует добавить строку в §11 ("break-glass action не переживает TTL и обязана иметь compensating review record").

### Validation
Integration test: активация break-glass вне scope политики отклоняется; активация в рамках политики создаёт TTL-bounded token и alert; истечение TTL отзывает права без ручного действия; отсутствие post-use review видно в dashboard спустя configurable порог.

---

## ADR-103: Модель классификации данных (data classification taxonomy)

```
Status: proposed
Date: 2026-07-20
Owners: Security, Legal
Related: B1 (IMPROVEMENT-PROPOSALS.md), OQ-007, FR-PRJ-005 (sensitivity), FR-MEM-001 (sensitivity), NFR-SEC-004/007
```

### Context
Четыре и более требования ссылаются на поле `sensitivity`/`classification`, но нигде не зафиксирован сам перечень допустимых значений и правил обращения с каждым. Без этого ADR реализация FR-PRJ-005/FR-MEM-001 будет придумывать enum ad hoc на этапе кода, что прямо противоречит "Definition of Ready" §15 SPECIFICATION ("входы... определены").

### Options and evidence
1. **Минимальная 3-уровневая модель**: `internal` / `confidential` / `restricted`. Просто, быстро внедряется, но не разделяет PII/regulated data как отдельный класс.
2. **4–5-уровневая модель** (например `public / internal / confidential / restricted / regulated`), где `regulated` явно триггерит дополнительные controls (data residency, DSAR eligibility) — точнее отражает связь с OQ-007/compliance, но требует явно определить, что относится к `regulated` до M1.
3. **Multi-dimensional tagging** (sensitivity level + data category: PII/financial/credentials/source-code) вместо одного enum — наиболее гибко, но заметно увеличивает сложность ACL/redaction логики на старте MVP.

### Decision (draft)
Рекомендуется вариант 2 как MVP-baseline (закрывает большинство сценариев из FR-MEM-001/FR-PRJ-005 без чрезмерной сложности), с явным резервированием варианта 3 как post-MVP расширения, если PII-специфичные требования (DSAR, право на удаление) потребуют более гранулярного тэгирования.

### Security/privacy/operational consequences
- `regulated` класс должен явно требовать более строгий default retention/export-контроль (пересекается с NFR-OPS-004, NFR-SEC-007).
- Неизвестный/незаданный класс не должен дефолтиться в `internal` молча — отсутствие классификации это отдельная, более строгая ветка (например блокирует indexing до классификации), а не "тихий default".

### Migration and rollback
Требует нового документа `docs/DATA-CLASSIFICATION.md` (раздел C IMPROVEMENT-PROPOSALS.md) и явного enum, на который затем ссылаются существующие FR без изменения их ID.

### Validation
Structural test (расширение `validate_spec.py`): каждое упоминание `sensitivity`/`classification` в SPECIFICATION.md резолвится к одному из объявленных в DATA-CLASSIFICATION.md значений.

---

## ADR-104: Egress allowlist на уровне Agent (не только Connector)

```
Status: proposed
Date: 2026-07-20
Owners: Security, Architecture
Related: G3 (IMPROVEMENT-PROPOSALS.md), FR-CON-004, §4.1 ARCHITECTURE trust boundary, ADR-005 (Connector sandbox, уже запланирован)
```

### Context
Connector как хост уже описан с explicit trust boundary (§4.1: только outbound, отдельные OS identities, redaction, spool). Но agent-specific network egress (какие внешние домены/IP конкретному agent разрешено вызывать через tools) не описан отдельно — сейчас предполагается, что весь egress, доступный Connector-хосту, доступен любому agent на нём, что избыточно широко относительно принципа least privilege, уже применённого к остальной системе (NFR-SEC-003 ASVS L2, §4.1 п.2 "минимальные права").

### Options and evidence
1. **Egress allowlist как часть Agent config** (аналогично `filesystem_scope` из FR-CON-004), enforced Connector-ом на уровне adapter process (например network namespace/firewall rule per agent process).
2. **Egress allowlist только на уровне Connector-хоста в целом** (текущее де-факто состояние) — минимум работы, но не масштабируется на multi-agent Connector хост с разными уровнями доверия к разным agent.
3. **Egress проверяется на уровне MCP/tool-declaration** (каждый MCP tool сам объявляет свой домен, Connector сверяет с allowlist per-tool, а не per-agent) — более гранулярно, но зависит от того, насколько MCP tools честно объявляют свои сетевые цели (недоверенный входной сигнал).

### Decision (draft)
Рекомендуется вариант 1 как baseline с возможностью уточнения через вариант 3 там, где MCP tool capability позволяет декларативно объявить domain — то есть 1 как enforced fallback, 3 как более точный сигнал поверх него, никогда не единственный источник правды.

### Security/privacy/operational consequences
Требует, чтобы ADR-005 (Connector sandbox baseline) явно включал network namespace/firewall enforcement per agent process, а не только filesystem/process isolation — стоит явно связать оба ADR при финализации ADR-005.

### Migration and rollback
Новое **FR-CON-008**, аддитивно к FR-CON-004; rollback — allowlist по умолчанию "весь egress хоста" (текущее поведение), пока функция не готова, явно помечено как temporary weaker baseline в OPEN-QUESTIONS.

### Validation
Adversarial test: agent с ограниченным allowlist не может инициировать соединение к произвольному внешнему домену через declared tool, попытка логируется как security event.

---

## Дополнения к `docs/OPEN-QUESTIONS.md` (для внесения при принятии соответствующих ADR)

| ID | Severity | Решение | Владелец | Deadline | Связано с |
|---|---|---|---|---|---|
| OQ-019 | BLOCKER | Compliance scope и юрисдикция (GDPR/CCPA/иное) | Security/Legal | До M1 | B2 |
| OQ-020 | MAJOR | Ownership/лицензия контента, сгенерированного агентами | Owner/Legal | До external distribution | G10 |
| OQ-021 | BLOCKER | Механика emergency stop (scope, кто активирует, circuit-breaker vs broadcast) | Security/Architecture | До M2 | A1 / ADR-101 |
| OQ-022 | BLOCKER | Break-glass access model (TTL, credential изоляция, review) | Security/Product | До M1 | H1 / ADR-102 |
| OQ-023 | BLOCKER | Таксономия классификации данных | Security/Legal | До M1 | B1 / ADR-103 |
| OQ-024 | MAJOR | Egress allowlist model для agent-level network scope | Security/Architecture | До M2 | G3 / ADR-104 |
| OQ-025 | MAJOR | Модель машинного доступа для внешних интеграций (API keys/OAuth) | Architecture/Security | До M3 | H4 |

---

## Как использовать этот документ

1. Каждый ADR здесь — draft для обсуждения, не решение. "Decision (draft)" — рекомендация автора ревью, не утверждённый выбор.
2. При принятии: перенести в `docs/adr/ADR-NNN-slug.md` с финальным номером (после того как заведена сама папка `docs/adr/`, см. раздел C `IMPROVEMENT-PROPOSALS.md`), проставить `Status: accepted`, добавить соответствующие FR/NFR/AT в `SPECIFICATION.md` и строки в `TRACEABILITY.md`.
3. Добавить соответствующие строки в `docs/OPEN-QUESTIONS.md` из таблицы выше (с исправленной опечаткой) и закрыть их по мере принятия ADR.
4. Прогнать `scripts/validate_spec.py` (и, если принято предложение F из `IMPROVEMENT-PROPOSALS.md`, — расширенную версию с проверкой traceability) перед commit.
