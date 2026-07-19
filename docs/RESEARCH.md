# Исследование интеграционных поверхностей

**Дата проверки:** 2026-07-19
**Статус:** source notes for Specification v0.1.0

## Метод

Проверялись официальные страницы продуктов и протоколов. Сведения ниже описывают доступную интеграционную поверхность на дату проверки, но не гарантируют стабильность API или наличие функции в конкретном тарифе/версии. Перед реализацией каждого адаптера обязательны pinned-версия, contract tests и повторная проверка документации.

## Проверенные источники

| Runtime | Подтверждённая поверхность | Проектное решение | Источник |
|---|---|---|---|
| Hermes Agent | HTTP API с `/v1/chat/completions`, `/v1/responses`, `/v1/runs`; session headers; отдельные profiles | Нативный HTTP adapter; capabilities определяются handshake, а не предположением | [Hermes API Server](https://hermes-agent.nousresearch.com/docs/user-guide/features/api-server), [Profiles](https://hermes-agent.nousresearch.com/docs/user-guide/profiles) |
| OpenClaw | Gateway protocol предоставляет status, channels, models, chat, agent, sessions, nodes и approvals; схема является источником точного контракта | Нативный Gateway adapter с pinned schema/version и reconnect/resume | [Gateway protocol](https://docs.openclaw.ai/gateway/protocol), [Gateway CLI](https://docs.openclaw.ai/cli/gateway) |
| Claude Code | Agent SDK документирует sessions, permissions, hooks, subagents и MCP | SDK adapter; permission/approval события нормализуются без обхода политики Claude | [Agent SDK overview](https://docs.anthropic.com/en/docs/claude-code/sdk/sdk-overview), [MCP](https://docs.anthropic.com/en/docs/claude-code/mcp) |
| OpenAI Codex | Для глубоких клиентов доступен app-server; также документированы SDK/headless use cases | App-server или SDK adapter после version-specific spike; CLI fallback только при структурированном выводе | [Codex App Server](https://learn.chatgpt.com/docs/app-server), [Codex resources](https://developers.openai.com/learn/codex) |
| OpenAI API / ChatGPT models | Responses API поддерживает conversation state; background mode допускает асинхронное выполнение | API adapter представляет API run, а не потребительский ChatGPT UI. Consumer ChatGPT account automation не входит в MVP | [Conversation state](https://platform.openai.com/docs/guides/conversation-state), [Background mode](https://platform.openai.com/docs/guides/background) |
| Gemini CLI | Документированы headless mode и MCP integration | Headless adapter с JSON output/exit semantics и explicit capability probe | [Gemini CLI](https://google-gemini.github.io/gemini-cli/), [Headless mode](https://google-gemini.github.io/gemini-cli/docs/cli/headless.html) |
| MCP | Стандартизирует discovery и вызов tools, resources и prompts | Используется как capability bridge, но не как полный lifecycle/session protocol | [Tools](https://modelcontextprotocol.io/specification/2025-06-18/server/tools), [Resources](https://modelcontextprotocol.io/specification/2025-06-18/server/resources), [Prompts](https://modelcontextprotocol.io/specification/2025-06-18/server/prompts) |

## Ограничения и выводы

1. **Нет универсальной семантики session/run/approval.** Нормализация должна сохранять vendor-specific payload в изолированном extension-поле и не скрывать потерю возможностей.
2. **MCP недостаточен для управления жизненным циклом агента.** Он полезен для tools/resources/prompts, но запуск, streaming, usage, cancel, checkpoint и resume задаются Agent Adapter Protocol.
3. **ChatGPT и OpenAI API — не одно и то же.** MVP не автоматизирует закрытый пользовательский UI ChatGPT и не извлекает из него токены/сессии.
4. **Лимиты не всегда доступны программно.** Connector принимает verified usage API, rate-limit headers, локальные метрики и ручные budget policies; приблизительные данные маркируются `estimated`.
5. **Handoff не переносит скрытые рассуждения.** Передаются только пользовательские сообщения, наблюдаемые tool results, проверенные факты, решения, артефакты, acceptance criteria и явно сформированный checkpoint.
6. **CLI-адаптеры рискованнее SDK/API.** Они требуют фиксированной версии, timeout/cancel contract, JSONL или иной структурированный канал, отдельный stderr и запрет parsing human UI как основного контракта.
7. **Capability negotiation обязательна.** UI не показывает resume, approvals, filesystem, terminal или usage как доступные, пока adapter handshake это не подтвердил.

## Неподтверждённые детали

Следующее не считается фактом до implementation spike:

- точная совместимость конкретных версий Codex app-server и Agent Control Center;
- полнота usage/quota API каждого провайдера;
- возможность безопасного resume после смены runtime без пользовательского checkpoint;
- лицензии на встраивание/redistribution каждого SDK и CLI;
- parity функций между personal, team и enterprise тарифами.
