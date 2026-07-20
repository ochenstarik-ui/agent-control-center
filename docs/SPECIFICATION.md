# Техническое задание: Agent Control Center

| Поле | Значение |
|---|---|
| Версия | 0.1.0-draft |
| Дата | 2026-07-19 |
| Статус | **Draft — implementation blocked** |
| Владелец решения | Product owner / operator |
| Нормативный документ | Этот файл |
| Поддерживающие документы | `ARCHITECTURE.md`, `RESEARCH.md`, `OPEN-QUESTIONS.md`, `adapters/HERMES.md`, `patterns/WORKER_ORCHESTRATION.md`, `patterns/CREDENTIAL_POOLS.md`, `operations/MONITORING.md`, `operations/BACKUP.md` |

> Разработка продукта не начинается до закрытия блокирующих решений, G1 PASS и явного утверждения оператором. Формулировки MUST/SHALL обязательны; SHOULD требуют обоснования отклонения.

## 1. Назначение

Agent Control Center (ACC) — единое рабочее пространство для управления проектами, задачами и долгоживущими серверными ИИ-агентами через Web, Desktop и Android. Система обеспечивает контролируемый перенос наблюдаемого контекста между разными runtime, общую проектную память, реестр skills и wiki, не пытаясь переносить скрытые рассуждения модели или обходить политики провайдеров.

### 1.1 Цели и метрики результата

| Цель | Метрика MVP |
|---|---|
| Единое управление | ≥95% поддерживаемых run lifecycle действий доступны из всех трёх клиентов |
| Безопасный handoff | ≥99% принятых handoff не теряют objective, acceptance criteria, decisions и artifact refs по contract test |
| Общий контекст | 100% memory/wiki/skill результатов показывают scope и provenance |
| Контроль рисков | 100% destructive/high-risk действий имеют audit event; policy-required действия требуют approval |
| Наблюдаемость | ≥99% нормализованных run events доставлены либо восстановлены после reconnect в пределах retention |
| Практичность | p95 открытия проекта ≤2 с, p95 появления live event ≤1,5 с при целевой нагрузке |

### 1.2 Не-цели MVP

- замена IDE, Git hosting, CI/CD, issue tracker или model provider;
- автоматизация закрытого consumer UI ChatGPT либо извлечение browser cookies/session tokens;
- перенос hidden chain-of-thought, provider-internal state или секретов между агентами;
- полностью автономное переключение на платный/привилегированный агент без policy/approval;
- marketplace публичных skills;
- iOS-клиент;
- кросс-региональный active-active control plane;
- гарантированно точный остаток квоты, если runtime не предоставляет authoritative API.

## 2. Пользователи и роли

| Роль | Основные задачи |
|---|---|
| Organization Owner | tenant settings, billing/budgets, SSO, retention, emergency access |
| Workspace Admin | участники, connectors, agent policies, project templates |
| Project Lead | проекты, priorities, approvals, handoff, authoritative memory/wiki |
| Operator | наблюдение и управление runs, incidents, Connector health |
| Contributor | задачи, диалоги, artifacts, drafts memory/wiki |
| Viewer/Auditor | read-only view, audit export в разрешённой области |
| Server Connector | machine identity; исполняет только подписанные/авторизованные commands |
| AI Agent | untrusted workload identity с ограниченными capabilities и scope |

RBAC задаёт базовые права; ABAC учитывает tenant/workspace/project, sensitivity, action risk, agent capability и device assurance.

## 3. Термины

- **Agent** — зарегистрированная конфигурация runtime/model/tools на конкретном Connector.
- **Connector** — сервис рядом с агентами, устанавливающий исходящее защищённое соединение с Control Plane.
- **Adapter** — versioned integration с конкретным runtime.
- **TaskRun** — логическая попытка выполнить задачу; содержит один или несколько RunAttempt.
- **RunAttempt** — исполнение на одном агенте/runtime.
- **Checkpoint** — наблюдаемый, provenance-aware снимок переносимого состояния.
- **Handoff** — контролируемое создание следующего attempt из checkpoint.
- **Memory entry** — версионируемая запись факта/решения/ограничения и т. п. с scope и provenance.
- **Skill** — версионируемый пакет инструкций/ресурсов и, опционально, исполняемых assets.
- **Wiki** — версионируемое проектное знание в Markdown.
- **Capability** — функция, явно подтверждённая adapter handshake.
- **Measured/estimated/unknown usage** — authoritative, вычисленная или недоступная информация о лимитах.

## 4. Scope и релизы

### 4.1 MVP

- multi-tenant control plane и OIDC/local bootstrap;
- Web/PWA, Desktop, Android с общим UX contract;
- workspaces/projects/Kanban tasks/dependencies/artifacts;
- enrollment Connector, registry agent, capability/health view;
- run start/stream/approval/cancel/checkpoint/manual handoff;
- adapters: Hermes, OpenClaw и минимум один SDK/CLI runtime после spike; generic adapter contract;
- memory, skill registry, wiki, search;
- usage/budget signals, notifications, audit, backup/restore.

### 4.2 Post-MVP

- policy-governed automatic fallback;
- workflows/DAG orchestration и scheduled runs;
- enterprise SCIM/advanced DLP/legal hold;
- iOS and richer native integrations;
- public/organization skill catalog;
- analytics, cost optimization and provider routing.

## 5. Предпосылки и зависимости

1. Connector host поддерживает безопасное service execution и outbound TLS.
2. Runtime уже установлен/лицензирован владельцем; ACC не распространяет его без прав.
3. Provider credentials остаются в Connector-side secret store либо approved secret manager.
4. Control Plane располагает PostgreSQL, object storage, durable queue и backup destination.
5. Push notifications зависят от platform services и являются best-effort дополнением, не source of truth.
6. Семантика adapters определяется pinned version и contract tests; исследование — в `RESEARCH.md`.
7. Блокирующие продуктовые решения перечислены в `OPEN-QUESTIONS.md`.

## 6. Функциональные требования

Формат каждой строки: приоритет; предусловия; основной flow; ошибки/edge cases; acceptance test. `P0` обязателен для MVP, `P1` желателен при сохранении срока, `P2` post-MVP.

### 6.1 Identity, access, tenancy

| ID | Pri | Предусловия | Требование и основной flow | Ошибки / edge cases | Acceptance |
|---|---:|---|---|---|---|
| **FR-IAM-001** | P0 | Новый deployment | Первый owner создаётся одноразовым bootstrap token; после первого успеха token инвалидируется | Повтор/expired token → 401 без user creation | **AT-FR-IAM-001:** второй вызов тем же token отклонён; ровно один owner и audit event |
| **FR-IAM-002** | P0 | Настроен IdP либо local auth | Login выдаёт short-lived access и rotating refresh credential, привязанный к device session | revoked/rotated credential → 401; replay отзывает credential family | **AT-FR-IAM-002:** rotation/replay integration test подтверждает отзыв и повторный login |
| **FR-IAM-003** | P0 | Actor состоит в tenant | Каждая операция проходит RBAC+ABAC и tenant scoping до чтения данных | IDOR/cross-tenant ID → 404, не раскрывая существование объекта | **AT-FR-IAM-003:** matrix test всех ролей и cross-tenant identifiers не обнаруживает утечек |
| **FR-IAM-004** | P0 | Risk policy требует approval | Создаётся approval с snapshot действия, approver scope и TTL; execution ждёт решение | self-approval запрещён политикой; expiry → blocked | **AT-FR-IAM-004:** high-risk command не доставлен Connector до валидного approval |
| **FR-IAM-005** | P1 | Пользователь управляет devices | Пользователь видит и отзывает device sessions; отзыв закрывает WS и refresh | offline client теряет write-доступ при следующей проверке | **AT-FR-IAM-005:** revoked device не обновляет task и получает auth event |

### 6.2 Connectors and agents

| ID | Pri | Предусловия | Требование и основной flow | Ошибки / edge cases | Acceptance |
|---|---:|---|---|---|---|
| **FR-CON-001** | P0 | Admin создал одноразовый enrollment token | Connector регистрирует machine identity, public key, labels и version через outbound TLS | token reuse/tenant mismatch → reject и security audit | **AT-FR-CON-001:** повтор enrollment и подменённый tenant отклоняются |
| **FR-CON-002** | P0 | Connector enrolled | mTLS WSS поддерживает heartbeat, reconnect, cursor resume и encrypted bounded spool | duplicate/out-of-order events дедуплицируются/упорядочиваются; gap отмечается | **AT-FR-CON-002:** network fault test восстанавливает ordered stream без двойных side effects |
| **FR-CON-003** | P0 | Adapter установлен | Handshake публикует adapter/runtime versions, identity и capabilities snapshot | неизвестная schema/version → incompatible, запуск запрещён | **AT-FR-CON-003:** UI/API скрывают unsupported actions и блокируют forged capability |
| **FR-CON-004** | P0 | Admin имеет доступ | Agent создаётся из Connector+adapter+runtime config+policy; secret хранится только как reference | secret в request/log/event → validation failure/redaction alert | **AT-FR-CON-004:** secret canary отсутствует в DB, API, audit и logs |
| **FR-CON-005** | P0 | Agent зарегистрирован | Health показывает online/degraded/offline/incompatible, last seen, latency и active runs | stale heartbeat переводит в offline без удаления агента | **AT-FR-CON-005:** state transitions происходят по заданным thresholds и видны всем клиентам |
| **FR-CON-006** | P0 | Команда готова к dispatch | Каждая command имеет idempotency key, lease, deadline, policy digest и optional approval token | expired lease/replay/policy mismatch → не исполнять, вернуть typed outcome | **AT-FR-CON-006:** повтор start/cancel не создаёт второй native run/side effect |
| **FR-CON-007** | P1 | Доступна совместимая версия | Admin выполняет staged Connector/adapter upgrade с drain и rollback | active run не прерывается forced update; failed health → rollback | **AT-FR-CON-007:** upgrade fault test возвращает previous healthy version |

### 6.3 Workspaces, projects, tasks and artifacts

| ID | Pri | Предусловия | Требование и основной flow | Ошибки / edge cases | Acceptance |
|---|---:|---|---|---|---|
| **FR-PRJ-001** | P0 | Authorized user | Создание workspace/project задаёт name, key, visibility, retention, default policies и wiki root | duplicate key → 409; invalid policy → 422 | **AT-FR-PRJ-001:** созданный project атомарно содержит defaults и audit event |
| **FR-PRJ-002** | P0 | Project существует | Task хранит title, description, status, priority, assignees, agent policy, acceptance criteria, labels, due date | stale revision → 409 с current revision | **AT-FR-PRJ-002:** optimistic concurrency не теряет параллельное изменение |
| **FR-PRJ-003** | P0 | Tasks существуют | Kanban поддерживает configurable columns, ordering, filters и bulk move в рамках policy | invalid transition/partial bulk → atomic reject с per-item reason | **AT-FR-PRJ-003:** одинаковый порядок/статусы наблюдаются Web/Desktop/Android |
| **FR-PRJ-004** | P0 | Tasks одного project | Dependencies образуют DAG; blocked task не стартует без authorized override | cycle/self-link → 422; deleted dependency сохраняет audit reference | **AT-FR-PRJ-004:** property test не позволяет создать цикл и корректно считает blocked |
| **FR-PRJ-005** | P0 | Actor имеет artifact permission | Artifact загружается multipart, получает hash, MIME, sensitivity, provenance и immutable version | hash mismatch/malware/policy violation → quarantine | **AT-FR-PRJ-005:** download проверяет ACL; изменённый blob не проходит integrity check |
| **FR-PRJ-006** | P1 | Есть Git integration | Project может хранить repository reference/branch/commit/PR metadata без provider secret | webhook replay/out-of-scope repo → reject | **AT-FR-PRJ-006:** task links commit metadata и не раскрывает integration token |

### 6.4 Runs, conversations, approvals and handoff

| ID | Pri | Предусловия | Требование и основной flow | Ошибки / edge cases | Acceptance |
|---|---:|---|---|---|---|
| **FR-RUN-001** | P0 | Task runnable; agent online/capable | User выбирает agent, ввод, context scopes и budget; система создаёт TaskRun/Attempt и dispatch command | offline/incompatible/budget blocked → typed blocked state, без native start | **AT-FR-RUN-001:** successful start создаёт одну lineage и ordered initial events |
| **FR-RUN-002** | P0 | Attempt active | Нормализованные events stream в реальном времени: text, tool, progress, usage, approval, artifact, status | disconnect использует cursor resume; unsupported event сохраняется как vendor extension | **AT-FR-RUN-002:** reconnect не дублирует события и сохраняет sequence |
| **FR-RUN-003** | P0 | User sends message | Conversation message immutable после отправки, допускает correction message; sensitivity/redaction применяются до dispatch | слишком большой input → 413 с limits; prohibited secret → block | **AT-FR-RUN-003:** correction сохраняет original/provenance и agent получает разрешённую версию |
| **FR-RUN-004** | P0 | Adapter запрашивает approval | UI показывает точный action, args diff, risk, expiry и target; approve/deny подписывается actor identity | changed args после approval → approval invalid; timeout → denied/blocked policy | **AT-FR-RUN-004:** TOCTOU test блокирует command с изменённым digest |
| **FR-RUN-005** | P0 | Attempt active | Cancel поддерживает graceful и force (при праве), показывает acknowledgement и terminal outcome | lost Connector → cancelling_pending; повтор cancel идемпотентен | **AT-FR-RUN-005:** cancel fault test не переводит в cancelled без подтверждения/timeout policy |
| **FR-RUN-006** | P0 | Attempt имеет observable state | Checkpoint формирует objective, criteria, messages, verified facts, decisions, completed/pending work, errors, artifact refs и source hashes | hidden reasoning/secrets исключаются; oversized bundle bounded с manifest omissions | **AT-FR-RUN-006:** schema/secret tests и human-readable preview проходят до handoff |
| **FR-RUN-007** | P0 | Checkpoint valid; target capable | Manual handoff показывает source/target, estimated cost/limits и preview; создаёт новый Attempt, target подтверждает ingestion, затем source lease закрывается | target reject/timeout → source остаётся resumable; lineage не разрывается | **AT-FR-RUN-007:** fault injection в каждой фазе не теряет runnable state и не запускает два writer lease |
| **FR-RUN-008** | P0 | Usage/budget signal изменён | На rate limit/quota система классифицирует signal, ставит run в blocked/handoff_ready и предлагает совместимые targets | estimated signal явно маркируется; неизвестное не показывается как zero | **AT-FR-RUN-008:** 429/headers/local budget/unknown дают разные корректные UI states |
| **FR-RUN-009** | P1 | Run terminal | User может retry from checkpoint, fork с изменённым context или close; lineage и cost сохраняются | retry non-idempotent completed steps требует explicit plan/approval | **AT-FR-RUN-009:** retry не помечает старый attempt active и предупреждает о side effects |

### 6.5 Shared memory and retrieval

| ID | Pri | Предусловия | Требование и основной flow | Ошибки / edge cases | Acceptance |
|---|---:|---|---|---|---|
| **FR-MEM-001** | P0 | Actor имеет write scope | Memory entry создаётся с kind, scope, provenance, verification, sensitivity, validity и content hash | отсутствующая provenance/запрещённый scope → 422/403 | **AT-FR-MEM-001:** запись без обязательных metadata не индексируется |
| **FR-MEM-002** | P0 | Entry существует | Update создаёт immutable version/supersedes link; concurrent contradiction создаёт conflict, не silent overwrite | stale revision → conflict response | **AT-FR-MEM-002:** concurrent property test сохраняет обе версии и conflict record |
| **FR-MEM-003** | P0 | Query authorized | Retrieval применяет ACL до lexical/semantic ranking, filters scope/time/type/verification и возвращает citations | недоступная запись не влияет даже через count/timing в заданном threat model | **AT-FR-MEM-003:** cross-scope leakage suite не находит content/metadata |
| **FR-MEM-004** | P0 | Context bundle строится | Context Broker выбирает bounded verified context по policy/token budget и записывает retrieval manifest | overflow сокращает низший приоритет и сообщает omissions | **AT-FR-MEM-004:** deterministic fixture даёт bounded bundle и воспроизводимый manifest |
| **FR-MEM-005** | P0 | Agent предлагает memory | Agent-created запись остаётся draft/unverified до policy либо human review | prompt injection не может повысить trust/scope | **AT-FR-MEM-005:** malicious artifact не создаёт authoritative memory |
| **FR-MEM-006** | P1 | Entry устарела/ошибочна | Authorized user revokes/expires/supersedes entry; прошлые runs сохраняют ссылку на использованную version | hard delete ограничен retention/privacy workflow | **AT-FR-MEM-006:** новый retrieval исключает revoked, старый manifest остаётся auditable |
| **FR-MEM-007** | P1 | Index повреждён/сменён | Derived vector/full-text index полностью перестраивается из authoritative source | rebuild failure не удаляет source; degraded search обозначен | **AT-FR-MEM-007:** empty-index restore даёт эквивалентный authorized result set |

### 6.6 Skills registry

| ID | Pri | Предусловия | Требование и основной flow | Ошибки / edge cases | Acceptance |
|---|---:|---|---|---|---|
| **FR-SKL-001** | P0 | Contributor имеет publish-draft | Skill version загружается с manifest, digest, provenance, compatibility и permission declaration; version immutable | digest mismatch/zip traversal/oversize → quarantine | **AT-FR-SKL-001:** malicious package corpus не выходит из scanner sandbox |
| **FR-SKL-002** | P0 | Version scanned | Reviewer видит diff, permissions, executable assets и sources; устанавливает approved/rejected/quarantined | author self-approval запрещается policy | **AT-FR-SKL-002:** executable skill нельзя активировать без required review |
| **FR-SKL-003** | P0 | Approved compatible version | Project/agent activation pin-ит exact version и grants; Adapter получает только разрешённый bundle | incompatible runtime/capability → blocked | **AT-FR-SKL-003:** update latest не меняет pinned active run |
| **FR-SKL-004** | P0 | Новая version опубликована | UI показывает semantic diff, risk changes и rollout; rollback возвращает предыдущий pin | revoked vulnerable version нельзя активировать заново | **AT-FR-SKL-004:** staged rollout/rollback сохраняет audit и deterministic resolution |
| **FR-SKL-005** | P1 | User ищет skill | Search/filter по owner, tags, compatibility, review state; results показывают trust/provenance | quarantined скрыт для non-admin | **AT-FR-SKL-005:** ACL/trust filters согласованы API и все клиенты |

### 6.7 Wiki

| ID | Pri | Предусловия | Требование и основной flow | Ошибки / edge cases | Acceptance |
|---|---:|---|---|---|---|
| **FR-WIK-001** | P0 | Project существует | Wiki page хранит Markdown, path/title, aliases, ACL, status draft/published и immutable revisions | path collision/stale revision → 409 | **AT-FR-WIK-001:** concurrent edit не теряет content и предлагает merge |
| **FR-WIK-002** | P0 | Pages/artifacts существуют | Backlinks, links и attachments резолвятся version-aware; broken links видимы | forbidden target не раскрывает title | **AT-FR-WIK-002:** link checker и ACL suite проходят на mixed-scope fixture |
| **FR-WIK-003** | P0 | Agent генерирует страницу | Generated content сохраняется draft с citations/provenance; authoritative publish требует policy review | unsupported citation → flagged, не published | **AT-FR-WIK-003:** agent не может самостоятельно повысить draft до authoritative |
| **FR-WIK-004** | P1 | Query authorized | Full-text/semantic search возвращает snippets, revision, scope и citations | stale index отмечается; ACL до ranking | **AT-FR-WIK-004:** index rebuild и leakage tests эквивалентны memory retrieval controls |

### 6.8 Usage, notifications and audit

| ID | Pri | Предусловия | Требование и основной flow | Ошибки / edge cases | Acceptance |
|---|---:|---|---|---|---|
| **FR-OPS-001** | P0 | Adapter/provider signal доступен | Usage Service нормализует units, window, reset, source и confidence measured/estimated/unknown | несопоставимые units не суммируются как одно значение | **AT-FR-OPS-001:** fixtures всех confidence states визуально/в API различимы |
| **FR-OPS-002** | P0 | Budget policy задана | Soft threshold уведомляет; hard threshold блокирует новый dispatch либо требует override approval | in-flight policy задаёт allow/checkpoint/cancel, не подразумевается | **AT-FR-OPS-002:** boundary tests на reset/race/timezone исполняют выбранную policy ровно один раз |
| **FR-OPS-003** | P0 | Event соответствует preference | In-app и push notification дедуплицируются, deep-link ведёт к объекту после auth | push failure не меняет authoritative state | **AT-FR-OPS-003:** duplicate event даёт одно notification; revoked user не получает content |
| **FR-OPS-004** | P0 | Security/lifecycle action | Append-only audit хранит actor/workload, action, target, result, policy, correlation, timestamp и safe diff | sensitive payload redacted; gap/tamper observable | **AT-FR-OPS-004:** audit completeness test покрывает auth, policy, run, handoff, skill и admin actions |
| **FR-OPS-005** | P1 | Auditor authorized | Filter/export audit формирует signed manifest и bounded export без запрещённых данных | oversized export асинхронен; expired link → 410 | **AT-FR-OPS-005:** export hash проверяется и obeys tenant/time/ACL boundaries |

## 7. Нефункциональные требования

### 7.1 Security and privacy

| ID | Требование | Проверка |
|---|---|---|
| **NFR-SEC-001** | TLS 1.3 предпочтительно, минимум TLS 1.2 по утверждённой policy; Connector mTLS; encryption at rest для DB/object/backup | **AT-NFR-SEC-001:** automated TLS/config scan и restore encrypted backup |
| **NFR-SEC-002** | Credentials только в approved secret store; API/log/audit/artifact проходят secret redaction; rotation без redeploy Control Plane | **AT-NFR-SEC-002:** canary secret e2e scan и rotation test |
| **NFR-SEC-003** | OWASP ASVS L2 baseline для web/API; mobile secure storage; desktop bridge allowlist и CSP | **AT-NFR-SEC-003:** SAST/DAST/dependency/mobile/desktop security gates без high findings |
| **NFR-SEC-004** | Tenant isolation enforced server-side and tested на direct IDs, search, events, exports, caches и vectors | **AT-NFR-SEC-004:** adversarial multi-tenant suite имеет zero cross-tenant disclosures |
| **NFR-SEC-005** | Prompt/tool output/artifacts считаются untrusted; provenance, quarantine, content-type validation, no instruction privilege escalation | **AT-NFR-SEC-005:** injection corpus не меняет policy/scope/approval state |
| **NFR-SEC-006** | Command replay protection, idempotency, signed policy/approval digest и server-authoritative time | **AT-NFR-SEC-006:** replay/TOCTOU/clock-skew suite не повторяет side effects |
| **NFR-SEC-007** | Data export/delete/privacy workflow с legal retention override; deletion tombstone и verified background purge | **AT-NFR-SEC-007:** lifecycle test подтверждает export completeness и purge по policy |
| **NFR-SEC-008** | SBOM, pinned dependencies, signed release artifacts и provenance; critical CVE policy блокирует release | **AT-NFR-SEC-008:** release gate проверяет SBOM/signature/provenance и policy thresholds |

### 7.2 Reliability, consistency and recovery

| ID | Требование | Проверка |
|---|---|---|
| **NFR-REL-001** | Production monthly availability target 99.5% без плановых окон; status component-wise | **AT-NFR-REL-001:** SLI calculation from synthetic checks and documented exclusions |
| **NFR-REL-002** | At-least-once command/event transport plus application idempotency; per-run ordering and explicit gap | **AT-NFR-REL-002:** chaos test disconnect/duplicate/reorder не повторяет side effects |
| **NFR-REL-003** | RPO ≤15 мин, RTO ≤4 ч для production profile; restore drill минимум ежеквартально | **AT-NFR-REL-003:** timed clean-environment restore meets RPO/RTO and integrity checks |
| **NFR-REL-004** | Run lease исключает двух concurrent writers; failover не заявляет success без runtime evidence | **AT-NFR-REL-004:** partition test preserves single-writer invariant |
| **NFR-REL-005** | Schema migrations resumable, backup-first, observable; совместимость server/client/Connector минимум N-1 | **AT-NFR-REL-005:** upgrade/rollback matrix N and N-1 passes with representative data |

### 7.3 Performance and capacity

Целевая MVP-нагрузка: 100 concurrent users, 50 connected Connectors, 500 registered agents, 200 concurrent runs, 10 000 projects, 1 000 000 tasks, 10 000 000 run events и 1 000 000 memory/wiki revisions на deployment. Увеличение требует capacity test, а не предположения линейности.

| ID | Требование | Проверка |
|---|---|---|
| **NFR-PERF-001** | p95 read API ≤500 мс, write acknowledgement ≤800 мс при target load, без provider runtime latency | **AT-NFR-PERF-001:** reproducible load profile; error rate <1% excluding intentional 4xx |
| **NFR-PERF-002** | p95 live event latency Connector→online client ≤1.5 с; reconnect catch-up 10k events ≤30 с | **AT-NFR-PERF-002:** instrumented streaming benchmark |
| **NFR-PERF-003** | Project/Kanban initial usable view p95 ≤2 с broadband и ≤4 с simulated 4G, warm cache | **AT-NFR-PERF-003:** Web/Desktop/Android performance test with declared devices |
| **NFR-PERF-004** | Search p95 ≤2 с на target corpus; context bundle p95 ≤3 с до runtime dispatch | **AT-NFR-PERF-004:** representative ACL-heavy corpus benchmark |

### 7.4 UX, accessibility and portability

| ID | Требование | Проверка |
|---|---|---|
| **NFR-UX-001** | Web соответствует WCAG 2.2 AA; keyboard, focus, contrast, screen-reader labels; native wrappers сохраняют semantics | **AT-NFR-UX-001:** automated scan + manual keyboard/screen-reader checklist on critical journeys |
| **NFR-UX-002** | Critical action показывает target, consequence, risk and status; destructive action требует confirmation/approval по policy | **AT-NFR-UX-002:** usability acceptance для run/cancel/handoff/skill activation/admin |
| **NFR-UX-003** | UI различает measured/estimated/unknown, queued/running/blocked/offline и stale/fresh data не только цветом | **AT-NFR-UX-003:** visual/accessibility state matrix passes |
| **NFR-PORT-001** | Web: последние 2 major Chrome/Edge/Firefox/Safari; responsive ≥360 CSS px | **AT-NFR-PORT-001:** browser matrix smoke/e2e |
| **NFR-PORT-002** | Desktop MVP: Windows 11, macOS current+previous, Ubuntu 24.04 LTS; final matrix утверждается ADR | **AT-NFR-PORT-002:** signed install/upgrade/uninstall and critical journeys per OS |
| **NFR-PORT-003** | Android MVP: API level определяется ADR, target current Play policy; degraded read cache offline, writes queued only для explicitly safe operations | **AT-NFR-PORT-003:** device/emulator matrix and offline conflict tests |
| **NFR-PORT-004** | Клиенты version-aware: unsupported server API получает upgrade-required, а не undefined behavior | **AT-NFR-PORT-004:** compatibility matrix N/N-1/incompatible versions |

### 7.5 Operations and observability

| ID | Требование | Проверка |
|---|---|---|
| **NFR-OPS-001** | Structured logs, metrics, traces с correlation/run/connector IDs; content/secrets excluded by default | **AT-NFR-OPS-001:** e2e trace links command to result; canary absent from telemetry |
| **NFR-OPS-002** | Alerts покрывают availability, queue lag, event gaps, Connector churn, auth anomalies, backup/restore, storage and error budgets | **AT-NFR-OPS-002:** alert tests reach on-call route with runbook links |
| **NFR-OPS-003** | Health/readiness различают process, dependencies and migration state; readiness false during unsafe state | **AT-NFR-OPS-003:** dependency fault matrix produces expected health codes |
| **NFR-OPS-004** | Retention configurable per tenant within operator bounds: audit ≥365d default, events 90d, artifacts/memory/wiki project policy, telemetry 30d; legal hold overrides purge | **AT-NFR-OPS-004:** time-travel retention suite validates purge/hold/export |
| **NFR-OPS-005** | Admin operations and incident recovery documented as executable runbooks; quarterly restore and Connector revocation drills | **AT-NFR-OPS-005:** fresh operator completes sampled runbooks without tribal knowledge |

## 8. UI/UX specification

### 8.1 Information architecture

Primary navigation: Home, Workspaces, Projects, Tasks, Runs, Agents, Memory, Skills, Wiki, Usage, Notifications; Admin adds Connectors, Members, Policies, Audit, System.

### 8.2 Critical screens

1. **Home:** assigned/blocked tasks, active runs, approvals, quota warnings, unhealthy Connectors.
2. **Project:** overview, Kanban/list, runs, artifacts, memory, skills, wiki, settings.
3. **Task detail:** requirements/criteria, dependencies, conversation, run timeline, agent selector, context preview, artifacts.
4. **Run console:** ordered event stream, status/usage, approvals, checkpoint/cancel/handoff controls, reconnect indicator.
5. **Handoff dialog:** reason, source/target capabilities, unavailable features, usage confidence, exact context preview/omissions, policy/approval impact.
6. **Agent registry:** runtime/adapter versions, Connector, health, capabilities, active work, limits, policy.
7. **Memory:** scope/type/trust filters, citations, conflicts, version history, revoke/supersede.
8. **Skills:** manifest/diff/permissions/trust, version pins, activation/rollout/rollback.
9. **Wiki:** tree/editor/preview/backlinks/history/citations/draft-publish state.
10. **Admin:** Connector enrollment/revocation, policies, audit and retention.

### 8.3 Client parity

Все клиенты MUST поддерживать read/triage, task updates, run observation, approvals и manual handoff. Server/Connector/retention/security administration MAY быть ограничено Web/Desktop, но Android показывает понятную причину и deep-link, а не скрывает существование операции.

### 8.4 Offline/conflicts

- Read cache показывает `last_synced_at` и может содержать только разрешённые non-secret данные.
- Offline write по умолчанию запрещён для approvals, run actions, policy, skill activation, membership и secrets.
- Safe task/wiki draft edits используют client mutation ID и base revision; conflict не разрешается last-write-wins молча.

## 9. API и event contract

Полный baseline endpoints описан в `ARCHITECTURE.md`. Общие правила:

- JSON UTF-8; version prefix `/v1`; UUID/ULID opaque IDs.
- Commands требуют `Idempotency-Key`; mutations возвращают revision/ETag.
- List: cursor pagination, stable ordering, bounded page size, explicit filters.
- Errors: `code`, localized-safe `message`, `correlation_id`, `retryable`, `details` без секретов.
- 401 — нет/истёк auth; 403 — известный actor без права; cross-tenant opaque object — 404; 409 — revision/state/idempotency conflict; 422 — semantic validation; 429 — rate/budget с source/confidence; 503 — dependency/runtime unavailable.
- WS events: schema version, globally unique ID, object/run sequence, timestamp, classification; client подтверждает cursor.
- Breaking change требует новой major API/AAP version и migration guide.

## 10. Data lifecycle

1. Authoritative records — PostgreSQL/object storage; search/vector — rebuildable derivatives.
2. Artifacts, wiki, memory и skills versioned; mutable metadata меняется optimistic concurrency.
3. Soft delete скрывает объект; purge идёт после retention/hold checks и создаёт non-sensitive tombstone.
4. Audit append-only; correction создаёт compensating event.
5. Backup охватывает DB, objects, encryption metadata, configuration manifests; секреты восстанавливаются отдельным approved process.
6. Tenant export включает schemas, versions, provenance and checksums, но не provider credentials/hidden reasoning.

## 11. State invariants

- Один TaskRun имеет не более одного writable active Attempt lease.
- Terminal Attempt не возвращается в active; retry/fork создаёт новый Attempt.
- Handoff не закрывает source resumability до подтверждения target ingestion.
- Capability используется только из актуального compatible handshake snapshot.
- Approval валиден только для exact action/policy/arguments digest и не переживает expiry/revocation.
- Memory/wiki/skill trust не повышается на основании инструкции внутри untrusted content.
- Cross-tenant references не существуют на уровне API, queue, cache, vector и export.
- `unknown` usage не преобразуется в `0` или `unlimited`.

## 12. Acceptance strategy и quality gates

### 12.1 Test layers

- unit/property tests: state machines, policies, DAG, idempotency, conflicts, redaction;
- contract tests: каждый AAP adapter против pinned runtime fixture;
- integration: DB/queue/object/Connector, auth, search, migration;
- e2e: Web/Desktop/Android critical journeys;
- security: tenant isolation, injection, replay, secrets, sandbox, supply chain;
- chaos/recovery: network partition, duplicate/reorder, process/DB/queue failure, restore;
- performance/accessibility/compatibility matrices;
- user acceptance на сценариях ниже.

Каждый `FR-*` и `NFR-*` имеет одноимённый `AT-*` в таблицах выше. CI/QA case может реализовать несколько AT, но отчёт MUST сохранять прямое отображение ID→результат→evidence.

### 12.2 End-to-end acceptance journeys

- **E2E-001 Onboarding:** owner bootstrap → IdP/local login → Connector enrollment → Hermes/OpenClaw agent discovery → capability view.
- **E2E-002 Project work:** project → dependent tasks → criteria → artifact → start run → live events → approval → success.
- **E2E-003 Quota handoff:** active run получает measured/estimated limit → checkpoint preview → manual compatible target → ingestion → continuation без duplicate writer.
- **E2E-004 Shared knowledge:** agent proposes memory/wiki draft → reviewer verifies → second agent retrieves citation → revoked version больше не попадает в новый context.
- **E2E-005 Skill lifecycle:** upload malicious/valid packages → quarantine/review → pin → staged activation → rollback.
- **E2E-006 Failure recovery:** Connector disconnect during run → spool/reconnect/cursor resume → no duplicate side effect → audit continuity.
- **E2E-007 Cross-client:** task/run started Web, approved Android, observed Desktop; state/revisions identical.
- **E2E-008 Tenant security:** attacker probes IDs/search/events/export/vector timing; no unauthorized disclosure.

### 12.3 Release gates

- G0 decisions: blocking open questions/ADRs approved.
- G1 requirements: completeness, traceability, measurable NFR, security/privacy review — PASS.
- G2 implementation: tests, independent review, migration/recovery evidence — PASS.
- P1 security: no unresolved critical/high; medium accepted by owner with expiry.
- P2 supply-chain/Watcher advisory: PASS or explicit operator disposition.
- P3 publish/deploy: exact candidate, clean tree, CI/evidence, rollback and explicit approval.

## 13. Delivery plan

| Milestone | Deliverable | Exit criteria |
|---|---|---|
| M0 Discovery/ADRs | decisions, threat model, UX prototypes, adapter spikes | all blocking questions closed; executable contract fixtures |
| M1 Platform skeleton | auth/tenant, project/task, audit, CI/CD, observability | isolation/security baseline and Web shell |
| M2 Connector/AAP | enrollment, command/event transport, Hermes/OpenClaw adapters | chaos/idempotency/compatibility tests pass |
| M3 Runs/handoff | console, approvals, checkpoint, manual handoff, usage | E2E-002/003/006 pass |
| M4 Knowledge | memory, skills, wiki, context broker | E2E-004/005 and leakage tests pass |
| M5 Clients | Desktop/Android wrappers, push/offline-safe flows | E2E-007 + platform/accessibility matrices |
| M6 Hardening/pilot | backup/restore, performance, runbooks, pilot migration | all gates, SLO evidence and operator sign-off |

Оценки срока/команды не фиксируются до M0 spikes и ADR; псевдоточные даты запрещены.

## 14. Риски и меры

| Риск | Влияние | Мера |
|---|---|---|
| Vendor API/CLI drift | adapter outage/data loss | pinned versions, capability handshake, contract CI, N-1 policy |
| Handoff semantic loss | повтор работы/ошибка | observable checkpoint schema, preview, provenance, target ack, lineage |
| Poisoned shared memory | persistent compromise | untrusted drafts, verification, provenance, ACL-before-retrieval, revoke |
| Skill supply chain | remote execution | quarantine, scanner, declared permissions, sandbox, signatures/review |
| Quota uncertainty | wrong routing expectation | measured/estimated/unknown, policies, no false precision |
| Secret leakage through agents | credential compromise | connector-side refs, redaction, DLP, least privilege, audit |
| Event duplication/partition | duplicate side effects | idempotency, leases, ordering, cursor, reconciliation |
| Cross-tenant search leak | privacy breach | server-side ACL before indexing/ranking, adversarial tests |
| Shared UI wrapper limitations | inconsistent UX/security | ADR/spike, narrow native bridge, parity contract |
| Scope expansion | delayed MVP | strict non-goals, P0/P1/P2, change-control and traceability |

## 15. Change control and Definition of Ready

Любое изменение P0 scope, trust boundary, data model, retention, API/AAP или supported platform требует обновить version, affected requirement IDs, ATs, risks, ADR/open question и migration impact.

Implementation task считается Ready только если:

- связана с утверждённым requirement/AT ID;
- входы, output, errors, permissions и telemetry определены;
- зависимости/миграция/rollback известны;
- test approach согласован;
- отсутствует unresolved blocking question;
- G1 не заблокирован.

## 16. Approval record

| Роль | Имя | Решение | Дата | Версия |
|---|---|---|---|---|
| Product owner/operator | — | Pending | — | 0.1.0-draft |
| Architecture | — | Pending | — | 0.1.0-draft |
| Security/privacy | — | Pending | — | 0.1.0-draft |
| Operations | — | Pending | — | 0.1.0-draft |
