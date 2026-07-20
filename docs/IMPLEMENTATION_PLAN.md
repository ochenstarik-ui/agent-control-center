# Agent Control Center — Статус реализации

**Дата:** 2026-07-20 | **Версия:** 0.1.0-alpha

## Что сделано

### Часть 1: Control Plane API ✅
**Репозиторий:** [agent-control-center-server](https://github.com/ochenstarik-ui/agent-control-center-server)
**Порт:** `localhost:8100`

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/health` | GET | Статус API |
| `/api/v1/runs` | POST | Запуск задачи на worker-профиле |
| `/api/v1/runs` | GET | Список задач (фильтр по agent) |
| `/api/v1/runs/{id}` | GET | Статус задачи |
| `/api/v1/agents/health` | GET | Проверка всех worker-профилей через 9Router |
| `/api/v1/agents/{id}` | GET | Инфо об агенте |
| `/api/v1/memory/{key}` | GET/PUT | Чтение/запись MEMORY.md |
| `/docs` | GET | Swagger UI |

### Часть 2: Web UI ✅
**URL:** `http://localhost:8100/ui`

**Сайдбар:**
- 🤖 **Агенты** — список worker-профилей (+добавление локальных агентов)
  - Зелёный/красный/оранжевый индикатор здоровья
  - Добавление агента: выбор провайдера → выбор модели → оркестрация
  - Оркестрация: авто-создание 4 субагентов (планировщик, разработчик, ревьюер, исследователь) с индивидуальными моделями
  - Редактирование субагентов (⚙), удаление агента
- 📁 **Проекты** — создание/редактирование/удаление
- 📋 **Задачи** — CRUD, отметка выполнения, привязка к проекту
- 👁 **Надзиратели** — мониторинг задач проекта + авто-оповещение при отказе агента

**Вкладки:**
- 💬 **Чат** — общение с выбранным агентом
- 🧠 **Память** — просмотр/запись MEMORY.md
- 👁 **Надзиратель** — лог событий надзирателя

**Провайдеры и модели:**
| Провайдер | Модели |
|-----------|--------|
| OpenCode Go | kimi-k2.7-code, kimi-k2.6, qwen3-coder, deepseek-v4-pro, gemini-3-flash, claude-sonnet-4 |
| ChatGPT/OpenAI | gpt-4.1, gpt-4o, gpt-4o-mini, o3, o4-mini |
| Gemini (Google) | gemini-2.5-pro, gemini-2.5-flash, gemini-3-flash-preview |
| NVIDIA | deepseek-v4-pro, llama-4-maverick, nemotron-5 |
| Ollama | llama3.3:70b, qwen3:32b, codestral:22b, deepseek-r1:32b |

### Часть 3: Desktop ✅
**Репозиторий:** [agent-control-center-desktop](https://github.com/ochenstarik-ui/agent-control-center-desktop)

- Electron-приложение, загружающее Web UI
- Сворачивается в трей (system tray)
- Ярлык на рабочем столе: «Agent Control Center»
- Использует существующий Electron из Hermes

### Часть 5: Supervisor Agent ✅
**Репозиторий:** [agent-control-center](https://github.com/ochenstarik-ui/agent-control-center) (scripts/supervisor.py)

- Мониторинг провайдеров через 9Router каждые 5 минут
- Авто-переключение worker-профилей на fallback при отказе
- Cooldown 30 минут между переключениями
- Восстановление на primary после 3 успешных проверок
- Уведомления в Telegram
- Запущен как cron: `hermes cron create "*/5 * * * *" --script supervisor.py --no_agent`

### Инфраструктура
- **9Router** — работает на `localhost:20127`, 25 подключений
- **Worker-профили** — 4 профиля (code, fast, research, review) через 9Router
- **Telegram-шлюз** — активен, `/sethome` настроен
- **WSL Ubuntu** — Docker 29.6.2 установлен, Postgres ожидает настройки

## Что осталось

### Часть 4: Android
- Capacitor-обёртка Web UI
- Push-уведомления
- Share intent

### Часть 6: Connector SDK
- Python-библиотека для подключения runtime (Hermes, OpenClaw, etc.)
- Регистрация capabilities
- Heartbeat и health-check

### Доработки UI
- Drag-and-drop задач между проектами
- Kanban-доска
- История запусков с логами
- Тёмная/светлая тема

### Доработки API
- PostgreSQL вместо in-memory хранилища
- Аутентификация пользователей
- WebSocket для real-time обновлений
