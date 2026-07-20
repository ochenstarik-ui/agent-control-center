# Предложения по доработке: Agent Control Center

| Поле | Значение |
|---|---|
| Тип документа | Non-normative review — предложения к `SPECIFICATION.md` v0.1.0-draft |
| Дата | 2026-07-20 |
| Статус | Draft для рассмотрения владельцем продукта/архитектуры |
| Действие | Ничего из этого не является утверждённым требованием. Принятие пункта требует: присвоить ID (FR-.../NFR-...), добавить AT, обновить `TRACEABILITY.md`, при необходимости завести ADR/OQ |

## 0. Общая оценка

Спецификация уже необычно зрелая для draft-стадии: закрытый список ролей, явные non-goals, DAG-инварианты, отдельный AAP-контракт с capability negotiation, checkpoint/handoff вместо "магического" переноса сессии, разделение measured/estimated/unknown usage, машинно проверяемая traceability (`validate_spec.py`), запрет на реализацию до G0/G1. Это редко встречается в спецификациях такого размера. Предложения ниже — это **пробелы и усиления**, а не переработка существующей структуры.

Категории: (A) отсутствующие функциональные возможности, (B) недостающие нефункциональные гарантии, (C) процессные/репозиторные документы, (D) уточнения к существующим требованиям, (E) риски, которые пока не названы, (G) второй проход по пробелам, (H) третий проход по пробелам.

---

## A. Функциональные пробелы

### A1. Emergency stop / global kill switch
Сейчас есть `cancel` на уровне одного Attempt (FR-RUN-005). Нет способа для Workspace Admin/Org Owner **мгновенно остановить все runs** в workspace/tenant (инцидент безопасности, скомпрометированный skill, runaway cost).
- Предлагаемое требование: **FR-SAF-001** — Admin может выполнить workspace-wide emergency stop; все active Attempt получают cancel c приоритетной lease-инвалидацией; новый dispatch блокируется до explicit unlock; действие само пишется в audit с наивысшим severity.
- Acceptance: emergency stop останавливает N параллельных runs за bounded time и не оставляет "zombie" writer lease.

### A2. Pre-dispatch cost/impact preview
Preview стоимости описан только для **handoff** (§8.2 п.5, FR-RUN-007). Для обычного старта run (FR-RUN-001) нет обязательного показа estimated cost/usage impact до dispatch.
- Предлагаемое: **FR-RUN-010** — перед стартом run с известным usage-provider показывается estimated cost/usage range (measured/estimated/unknown, как в FR-OPS-001); запуск с `unknown` cost требует explicit acknowledgement, если budget policy это требует.

### A3. Параллельная работа нескольких агентов над одной задачей
Текущая модель — один writable Attempt на TaskRun (инвариант §11) и последовательный handoff. Нет описания сценария "агент А делает backend, агент Б — тесты, для одной задачи параллельно" (multi-agent collaboration), который часто нужен именно в "control center" для агентов.
- Предлагаемое: явно закрепить как **non-goal MVP** (если это осознанный выбор) в §1.2, либо добавить **FR-RUN-011** (post-MVP) для параллельных sibling-Attempt с разделяемым read-only checkpoint и явным merge-review перед объединением в задачу. Сейчас это просто не упомянуто ни как non-goal, ни как roadmap-пункт — двусмысленность стоит закрыть явно.

### A4. Dry-run / plan-only режим
Нет режима, где агент строит план и список предполагаемых действий (особенно destructive: git push, file delete, external API call) **без исполнения**, для approval до реального запуска.
- Предлагаемое: **FR-RUN-012** — если capability `plan_mode` присутствует в handshake, run может стартовать в `plan_only`; approval экрана показывает предполагаемые действия; переход в исполнение — отдельная explicit команда.

### A5. Данные для чарджбэка/финансового учёта
OQ-012 фиксирует нормализацию usage/cost как открытый вопрос, но нет функционального требования на **cost attribution по project/workspace для финансовой отчётности** (не просто UI usage summary, а экспортируемый ledger).
- Предлагаемое: **FR-OPS-006** — Usage Service агрегирует normalized cost по project/workspace/agent за период и предоставляет exportable ledger с explicit confidence per entry; несопоставимые единицы не сворачиваются в одну сумму (согласуется с §11 инвариантом).

### A6. Webhook-безопасность для Git-интеграции
FR-PRJ-006 упоминает webhook replay protection, но не описывает **verification механизм** (HMAC signature, source IP allowlist, timestamp window) как отдельное требование — сейчас это спрятано в "edge cases" одной строки.
- Предлагаемое: расширить FR-PRJ-006 или добавить **NFR-SEC-009** — входящие webhook проверяются подписью провайдера и временным окном до постановки в очередь; невалидная подпись логируется как security event, не как обычная ошибка.

### A7. Explicit "definition of done" / task templates
Task хранит acceptance criteria как свободный текст (FR-PRJ-002). Нет structured template по типу задачи (bug/feature/research), что снижает единообразие качества handoff (FR-RUN-006 checkpoint зависит от чётких criteria).
- Предлагаемое: **FR-PRJ-007** (P1) — Project может определить task templates с обязательными полями acceptance criteria; создание задачи из template валидирует заполненность полей перед переводом в runnable-статус.

### A8. Приостановка/пауза run без cancel
Есть только running → cancelling → cancelled и checkpoint/handoff. Нет "мягкой" паузы (agent просто ждёт, ресурсы не освобождаются, но и работа не идёт) для случаев "я сейчас проверю approval вручную, не хочу терять контекст, но и не хочу formal handoff".
- Предлагаемое: рассмотреть **FR-RUN-013** (P2) — pause/resume в рамках одного Attempt, если capability поддерживает; иначе явно закрыть вопрос как non-goal, чтобы не осталось implicit ожидания у пользователей.

---

## B. Нефункциональные пробелы

### B1. Классификация данных не определена
OQ-007 помечает "classification/retention" как blocker, но нигде в репозитории нет самого перечня классов (public/internal/confidential/restricted/secret) и их дефолтных правил обращения — на них ссылаются NFR-SEC-004/007, FR-PRJ-005 (`sensitivity`), FR-MEM-001 (`sensitivity`), но словарь классов не задан.
- Предлагаемое: новый документ `docs/DATA-CLASSIFICATION.md` (см. раздел C) + **NFR-SEC-009** — каждая сущность с полем sensitivity/classification обязана резолвиться к одному из объявленных enum-классов; неизвестный класс блокирует запись, а не дефолтится в "internal".

### B2. Compliance framework не назван
Много "privacy/legal hold" ссылок (NFR-SEC-007, NFR-OPS-004), но нет явной привязки к конкретным режимам (GDPR/CCPA/аналог для целевого рынка), хотя это определяет DSAR-сроки, data residency и right-to-erasure semantics.
- Предлагаемое: добавить строку в §5 "Предпосылки" — целевой compliance scope определяется ADR до M1 (можно завести **OQ-019 BLOCKER** "Compliance scope и juridiction").

### B3. Целостность audit log не гарантирована криптографически
FR-OPS-004/NFR-OPS требуют "append-only" и "gap/tamper observable", но нет требования к **hash-chaining или WORM-хранилищу**, что обычно ожидается от audit trail в security-чувствительной системе такого рода.
- Предлагаемое: усилить NFR-SEC (например **NFR-SEC-010**) — audit events образуют verifiable hash chain или пишутся в WORM storage; периодическая integrity-проверка chain — отдельная runbook-процедура.

### B4. Локализация как архитектурное, а не только продуктовое решение
OQ-017 — MINOR, "branding/localization". Но i18n-архитектура (строки, RTL, форматы дат/чисел, локализация error-messages из §9 "localized-safe message") влияет на API contract уже в MVP, не только на бренд.
- Предлагаемое: поднять степень серьёзности до **MAJOR** и явно связать с §9 (error envelope) и NFR-UX; либо явно зафиксировать "MVP UI — только английский/русский, error message localization post-MVP" как non-goal в §1.2, чтоббы не было implicit ожиданий.

### B5. Red-teaming/adversarial testing cadence не определена
NFR-SEC-005 требует, чтобы prompt injection не повышал privilege, есть AT с "injection corpus". Но нет regular cadence (например quarterly red-team на новые skill/adapter версии) — только "release gate"-проверка.
- Предлагаемое: добавить в **NFR-OPS-005** (или новый NFR-SEC-011) периодический (например quarterly) adversarial review нового adapter/skill класса, не только at release.

### B6. Доступность (accessibility) вне Web
NFR-UX-001 требует WCAG 2.2 AA только для Web, "native wrappers сохраняют semantics" — расплывчато для Desktop/Android, где нет измеримого acceptance theshold.
- Предлагаемое: уточнить NFR-UX-001 explicit acceptance для Desktop (платформенные accessibility API: UI Automation/NSAccessibility) и Android (TalkBack) с отдельным AT, а не общей фразой "сохраняют semantics".

### B7. SLA на approval latency
FR-RUN-004/IAM-004 описывают механику approval, но нет требования к **времени ожидания и эскалации** (кто оповещается, если approval висит N минут на критичном run) — это либо в Notification Service, либо теряется.
- Предлагаемое: **NFR-OPS-006** — approval requests старше configurable threshold эскалируются дополнительному approver/on-call через notification; run остаётся blocked, но статус ожидания видим всем клиентам.

---

## C. Документы, которых не хватает в репозитории

| Файл | Зачем | Приоритет |
|---|---|---|
| `SECURITY.md` | Политика раскрытия уязвимостей (для приватного репо это тоже нужно на будущее external distribution по OQ-010); канал контакта, expected response time | до publish/G0 |
| `docs/DATA-CLASSIFICATION.md` | Перечень классов чувствительности и правил (см. B1), на который ссылаются уже 4+ FR/NFR | до M1 (закрывает OQ-007) |
| `docs/GLOSSARY.md` | §3 SPECIFICATION уже даёт термины, но по мере роста ADR/OQ словарь стоит вынести отдельно и валидировать, что новые термины не вводятся без определения | опционально, снижает риск дрейфа терминологии |
| `CHANGELOG.md` | Версия документа сейчас меняется (0.1.0-draft), но нет истории причин изменений — при частых ADR это станет проблемой ревью | с первого ADR |
| `docs/adr/ADR-000-template.md` + папка `docs/adr/` | ARCHITECTURE.md §11 перечисляет 6 обязательных ADR, но нет папки/шаблона под них — сейчас только generic decision template живёт в `OPEN-QUESTIONS.md` | до M0 |
| `CODE_OF_CONDUCT.md` | Не критично для solo-owner, но нужно до появления внешних контрибьюторов (упомянуто OQ-010 "third-party redistribution") | до external distribution |

---

## D. Уточнения к существующим требованиям

1. **FR-CON-007 (staged upgrade)** — не сказано, что происходит с in-flight approval token при upgrade adapter mid-flight; стоит явно указать, что approval digest инвалидируется при смене adapter_version, а не молча переносится.
2. **FR-MEM-004 (Context Broker bounded bundle)** — "сокращает низший приоритет" не определяет, как приоритет назначается по умолчанию (recency? verification_state? explicit pin?). Стоит зафиксировать default ranking algorithm хотя бы на уровне принципа (например: verified > unverified, explicit pin > recency > semantic score), иначе это будет решаться ad hoc при реализации.
3. **NFR-PERF-004 (context bundle p95 ≤3с)** — не указано поведение при превышении: жёсткий timeout с `unknown`-статусом или деградация до меньшего bundle. Стоит уточнить, что превышение timeout эквивалентно declared omission (согласуется с FR-MEM-004), а не silent failure.
4. **FR-SKL-002 (reviewer видит diff)** — "author self-approval запрещается policy" сформулирован как policy-требование, но не как system-enforced invariant в §11 (State invariants). Учитывая, что там уже есть похожий принцип для FR-IAM-004, стоит добавить строку в §11: "Skill version не может быть approved тем же actor, кто её опубликовал".
5. **§8.4 Offline/conflicts** — "Safe task/wiki draft edits" не перечисляет explicit whitelist того, что считается safe; в NFR-PORT-003 упомянуто "explicitly safe operations", но сам список не зафиксирован нигде как artifact — это ровно то, что должно быть в OQ-011, но сейчас там просто "exact allowlist TBD". Стоит добавить хотя бы starter-список (например: task description draft edit, comment draft, wiki draft paragraph) как non-blocking baseline, который OQ-011 может сузить/расширить, а не оставлять полностью пустым до M5.
6. **Capacity targets (§7.3)** — "10 000 000 run events... на deployment" — не указано ожидаемое **распределение по времени** (burst vs steady state), что важно для NFR-PERF-002 (reconnect catch-up 10k events ≤30с). Стоит явно указать, относится ли 10k к одному run или ко всему reconnect-объёму сразу после incident на нескольких runs.

---

## E. Риски, которых нет в таблице §14

| Риск | Влияние | Предлагаемая мера |
|---|---|---|
| Runaway cost от зацикленного агента без hard stop (см. A1/A2) | Финансовый/репутационный ущерб | Emergency stop + pre-dispatch cost preview + hard budget ceiling независимо от soft/estimated confidence |
| Скрытый vendor lock-in через AAP-специфичные vendor_extension поля, на которые начинает молча полагаться UI | Потеря portability между runtime | Explicit lint/CI правило: UI core не может рендерить `vendor_extension` как first-class control без явной feature-flag маркировки как non-portable |
| Drift между `TRACEABILITY.md` и реальным содержимым SPECIFICATION.md при ручных правках | Ложное чувство полноты покрытия | Расширить `validate_spec.py`: проверять, что каждый FR/NFR ID из SPECIFICATION.md встречается хотя бы один раз в TRACEABILITY.md (сейчас скрипт не читает TRACEABILITY.md вообще) |
| Одна доминирующая роль (Org Owner) одновременно управляет billing, emergency access и retention — недостаточная segregation of duties | Insider risk / single point of failure для approvals | Явно рассмотреть в OQ-009 dual-control для emergency access/retention override, не только для "destructive actions" в общем смысле |

---

## F. Небольшое расширение `validate_spec.py` (предложение, не реализовано)

Валидатор уже проверяет FR/NFR ↔ AT соответствие внутри `SPECIFICATION.md`, но **не** проверяет:
1. что каждый ID из `SPECIFICATION.md` действительно упомянут в `TRACEABILITY.md` (см. риск в разделе E);
2. что каждый `OQ-###` из `OPEN-QUESTIONS.md` с severity `BLOCKER` привязан хотя бы к одному `FR-`/`NFR-`/ADR упоминанию где-либо в `docs/`;
3. что новые файлы из раздела C (если приняты) присутствуют, аналогично текущему `REQUIRED_FILES`.

Это усиление логично сделать одним PR вместе с принятием любого пункта из разделов A–D, чтобы traceability не деградировала по мере роста количества требований.

**Проверено на практике:** черновик такого расширенного валидатора (`validate_spec_extended_DRAFT.py`, приложен отдельным файлом) уже сейчас, без единой правки в `SPECIFICATION.md`, находит реальный дрейф в текущем репозитории:
- 15 NFR/FR-ID (`FR-OPS-003`, весь блок `NFR-OPS-*`, `NFR-PERF-*`, `NFR-REL-*`, `NFR-PORT-004`) присутствуют в `SPECIFICATION.md`, но не упомянуты явно в `TRACEABILITY.md` — то есть traceability matrix уже сейчас не 1:1 с требованиями, хотя её статус заявлен как "запрос → нормативные требования".
- 8 `BLOCKER`-вопросов (`OQ-001, 002, 003, 006, 007, 008, 009, 010`) нигде за пределами `OPEN-QUESTIONS.md` не упоминаются — ни в `SPECIFICATION.md`, ни в `ARCHITECTURE.md`, ни в `TRACEABILITY.md`, что делает их источник в спецификации непрослеживаемым: неясно, какая конкретно строка требований зависит от их закрытия.

Это не гипотетический риск из раздела E — это уже так в текущей версии 0.1.0-draft, и стоит закрыть до G1.

---

## G. Второй проход: ещё не названные пробелы

### G1. Session recording / run replay для расследований
Audit (FR-OPS-004) фиксирует action/target/result, но нет требования к **полному воспроизведению** того, что именно видел агент в конкретном run (порядок событий, tool calls, approvals) для post-incident разбора — не как "лог одной строкой", а как replay в UI, эквивалентный тому, что видел оператор в реальном времени.
- Предлагаемое: **FR-OPS-007** — терминальный/активный run воспроизводим в Run Console read-only режиме из сохранённых `RunEvent` без повторного обращения к runtime; append-only инвариант уже задан §10, здесь нужен именно UI/API acceptance на replay.

### G2. Rate limiting и anti-abuse для самого Control Plane API
NFR-PERF задаёт целевые p95, FR-OPS-002 — budget policy на agent usage. Но нет требования по **защите API Gateway от abuse** (brute-force login, scraping через list endpoints, chatty polling клиента) независимо от provider-квот.
- Предлагаемое: **NFR-SEC-012** — per-actor/per-IP rate limiting на auth и list/search endpoints с 429 и `retryable`, независимо от agent budget policy; порог конфигурируем per tenant tier.

### G3. Egress-scope агента отдельно от Connector-scope
§4.1 ARCHITECTURE описывает trust boundary Connector (no secrets, redaction, sandbox), а capability `filesystem_scope` упомянута в §4.2. Но нет отдельного явного требования на **network egress allowlist на уровне конкретного Agent**, а не только Connector-хоста в целом — сейчас неверно настроенный/скомпрометированный агент может использовать любой egress, доступный Connector.
- Предлагаемое: расширить FR-CON-004 или добавить **FR-CON-008** — Agent конфигурация включает egress allowlist (domains/IP ranges), Connector enforces его на уровне adapter process, а не полагается на agent-level "честность" tool-вызовов.

### G4. Провайдерская zero-retention / no-training гарантия как явный критерий выбора adapter
`RESEARCH.md` описывает интеграционные поверхности, но не фиксирует, обучается ли провайдер на переданных данных / retention policy провайдера — это важно для тенанта с чувствительными данными и должно влиять на выбор adapter в OQ-005.
- Предлагаемое: добавить колонку/пункт в `RESEARCH.md` "data retention / training use по провайдеру, дата проверки" и явное требование **NFR-SEC-013** — Agent registration отображает известный retention/training-статус провайдера (known/unknown), `unknown` не трактуется как "no training".

### G5. Версионирование и аудит system prompt / инструкций агента
Skill версионируется (FR-SKL-*), но собственные instructions/system prompt конкретного Agent (не skill, а базовая конфигурация "как вести себя") нигде явно не версионируются и не проходят review — это тот же класс риска (poisoned instructions), что и skills, но без контроля.
- Предлагаемое: **FR-CON-009** — agent instructions/system prompt хранятся как immutable versioned config наравне с остальным agent config (FR-CON-004), изменение создаёт новую версию с diff, видимым Project Lead/Admin.

### G6. Explicit человеческий takeover активного run
Есть approve/deny и cancel, но нет "взять управление вручную" — оператор временно перехватывает conversation/terminal конкретного Attempt, не создавая handoff и не отменяя run (частый сценарий: агент застрял, но контекст терять не хочется).
- Предлагаемое: **FR-RUN-014** (P1/P2) — если capability поддерживает interactive intervention, оператор может отправить direct message в активный Attempt вне обычного conversation flow, помечается как human-injected в audit/timeline.

### G7. Outbound webhooks / события для внешних систем
Notification Service (§3 ARCHITECTURE) — только in-app/push/email. Нет исходящего webhook/интеграции с внешними системами (Slack/PagerDuty/generic HTTP) для critical events (approval needed, run failed, budget exceeded) — обычная потребность control-plane продукта такого рода.
- Предлагаемое: **FR-OPS-008** (P1, может быть post-MVP) — tenant может настроить outbound webhook subscription на подмножество событий с HMAC-подписью исходящего payload и retry/backoff; секреты webhook-получателя хранятся как reference, не в конфиге открытым текстом.

### G8. Deprecation/sunset policy для adapters и AAP версий
§9 ARCHITECTURE описывает N-1 совместимость клиент/сервер, но нет аналогичной политики для **adapter/AAP версий**, когда vendor discontinues старую версию API/CLI раньше, чем ACC успевает мигрировать.
- Предлагаемое: добавить в §11 ARCHITECTURE явную политику: adapter version получает `deprecated` статус с обязательным migration window до `unsupported`; runs на deprecated adapter показывают предупреждение, а не просто продолжают работать до внезапного отказа.

### G9. Демо/seed-данные и staging tenant
Delivery plan (§13 SPECIFICATION) не упоминает отдельный staging/sandbox tenant для тестирования upgrade Connector/adapter или демонстрации продукта без риска для production данных.
- Предлагаемое: **NFR-OPS-007** — deployment профиль поддерживает изолированный non-production tenant с synthetic seed-данными для staged upgrade validation перед production rollout (согласуется с "staged, signed, rollback-capable" из §9 ARCHITECTURE).

### G10. IP-собственность artifacts, сгенерированных агентом
Ни одно требование не фиксирует, кому принадлежит контент, сгенерированный AI Agent (код, wiki-страницы, artifacts) — это скорее legal/OQ-вопрос, чем FR, но сейчас не упомянут вообще, а он напрямую завязан на OQ-010 (license/business model).
- Предлагаемое: добавить **OQ-020 (MAJOR)** — "Ownership/license сгенерированного агентами контента" с owner Legal, deadline до external distribution.

---

## H. Третий проход: ещё не названные пробелы

### H1. Break-glass emergency access — процедура, а не только роль
В §2 у Organization Owner заявлена "emergency access", но нигде не описано **как** он ей пользуется: обходит ли она RBAC/ABAC, логируется ли отдельно, есть ли time-boxing и обязательный post-use review. Сейчас это просто слово в таблице ролей.
- Предлагаемое: **FR-IAM-006** — break-glass доступ активируется explicit действием с ограниченным TTL, генерирует audit event высшего severity немедленно (не post-factum), и требует обязательного review другим Admin/Owner после использования; сам факт наличия неиспользованного break-glass доступа виден в security dashboard.

### H2. Конфликт "policy заблокировала — человек хочет override"
FR-OPS-002 (budget) и общий approval flow подразумевают, что policy может заблокировать действие. Не описано, может ли уполномоченный человек **осознанно обойти** policy-блок (emergency override) и как это отличается от обычного approval — сейчас неясно, blocked означает "жёстко нельзя" или "нужен approval".
- Предлагаемое: уточнить в FR-OPS-002/FR-IAM-004, что policy-block и approval-required — разные состояния; override policy-block (не approval) требует отдельного явно более высокого права и создаёт audit-запись с пометкой "policy overridden by <actor>", отличимую от обычного approval.

### H3. Приватность staging/demo данных
G9 предложил staging tenant с synthetic-данными, но не сказано explicit, что **production данные не могут копироваться** в staging/demo без anonymization — иначе staging тихо становится вторым local production copy с более слабыми контролами.
- Предлагаемое: усилить NFR-OPS-007 (или новый NFR-SEC-014) — перенос данных production → non-production запрещён без документированной anonymization/synthetic-generation процедуры; сам перенос — auditable action.

### H4. Программный доступ для внешних интеграций (developer API keys / OAuth)
Весь §9 API baseline описан в терминах клиентских сессий (device session, refresh credential). Нет отдельной модели для **машинного доступа третьих сторон** (CI pipeline дергает ACC API, внешний BI дергает Usage Service) — другая identity-модель, чем DeviceSession, и её просто нет.
- Предлагаемое: **FR-IAM-007** (P1) — tenant может выпускать scoped API keys/OAuth client credentials для service-to-service доступа, с собственным rate limit, expiry и revocation, отдельно от DeviceSession/refresh flow.

### H5. Теневой (shadow) режим для новой версии adapter
FR-CON-007 покрывает staged upgrade с drain/rollback, но это переключение "было/стало". Нет режима, где новая версия adapter **параллельно** обрабатывает те же входы без реального effect (dry validation на реальном трафике) перед тем, как ей начинают доверять реальные commands.
- Предлагаемое: **FR-CON-010** (P2) — новая adapter version может быть активирована в shadow mode: получает copies команд, публикует события в отдельный non-authoritative канал для сравнения с текущей активной версией, не исполняя реальных side-effect действий.

### H6. Внешняя status-страница инцидентов
NFR-OPS-002 покрывает alerts на on-call. Нет ничего про **внешнюю коммуникацию с тенантами** во время инцидента (status page, incident timeline, post-mortem publication) — обычно ожидаемая часть Operations для B2B control-plane продукта.
- Предлагаемое: **NFR-OPS-008** — production profile поддерживает публичный/tenant-facing status component с историей инцидентов и связкой к внутренним SLI (NFR-REL-001), без утечки internal diagnostic данных.

### H7. Explicit единица версионирования самого AAP-протокола отдельно от adapter
§4.2 ARCHITECTURE вводит `schema_version` в envelope, но не описывает **политику эволюции самого AAP** (какие изменения minor/patch, какие требуют новой major-версии, сколько версий Connector Gateway обязан поддерживать одновременно) — это отдельная ось от "adapter version" (G8) и от "N-1 client/server" (§9).
- Предлагаемое: добавить в §11 ARCHITECTURE явную SemVer-политику для AAP schema с указанием, сколько major-версий Gateway поддерживает параллельно, и что breaking AAP change требует того же migration-guide процесса, что и API (§9 SPECIFICATION).

### H8. Доверие к самоотчётной уверенности агента в checkpoint
FR-RUN-006 требует "verified facts" в checkpoint, FR-MEM-005 разделяет verified/unverified для memory. Но для checkpoint не сказано explicit, как система отличает "агент сам сказал, что уверен" от "человек/policy подтвердили" — тот же класс проблемы, что unverified memory, но применительно к checkpoint-fact.
- Предлагаемое: уточнить FR-RUN-006 — каждый verified fact в checkpoint несёт то же поле `verification_state`/provenance, что и MemoryEntry (§7 ARCHITECTURE), а не отдельную непересекающуюся модель доверия.

### H9. Лимиты и autoarchival для артефактов на масштабе
Capacity targets (§7.3) считают tasks/events/revisions, но не artifacts (объём object storage) и не описывают tiering (hot/cold) при росте — для 10 000 проектов с бинарными artifacts это может быть доминирующей cost-статьёй, не отражённой ни в одном NFR.
- Предлагаемое: добавить target в §7.3 (например размер object storage на deployment) и **NFR-OPS-009** — artifacts старше configurable порога переводятся в cold storage tier автоматически, доступ остаётся, но с иной latency SLA, явно отличной от NFR-PERF-001.

---

## Как использовать этот документ

Ничего здесь не превращается в требование автоматически. Рекомендуемый процесс:
1. Владелец продукта/архитектуры помечает принимаемые пункты.
2. Для каждого принятого пункта — присвоить финальный ID, вставить в `SPECIFICATION.md`/`ARCHITECTURE.md` в соответствующий раздел, добавить AT.
3. Обновить `docs/TRACEABILITY.md`.
4. Если пункт меняет security boundary/API/data model — завести ADR или пункт в `OPEN-QUESTIONS.md` по правилам `CONTRIBUTING.md`.
5. Прогнать `scripts/validate_spec.py` — PASS обязателен перед commit.
