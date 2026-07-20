# Handoff Contract v1

**Версия:** 0.1.0-draft | **Статус:** Draft

## Назначение

Контракт определяет формат передачи контекста между агентами при handoff.
Гарантирует, что принимающий агент получает минимально достаточный bounded context
для продолжения работы без повторного исследования.

## JSON Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://agent-control-center/schemas/handoff-v1.json",
  "type": "object",
  "required": ["handoff_id", "from_agent", "to_agent", "objective", "bundle"],
  "properties": {
    "handoff_id": { "type": "string", "format": "uuid" },
    "version": { "const": "1.0" },
    "timestamp": { "type": "string", "format": "date-time" },
    
    "from_agent": {
      "type": "object",
      "required": ["agent_id", "runtime"],
      "properties": {
        "agent_id": { "type": "string" },
        "runtime": { "enum": ["hermes", "openclaw", "claude", "codex", "gemini"] },
        "model": { "type": "string" },
        "run_id": { "type": "string" }
      }
    },
    
    "to_agent": {
      "type": "object",
      "required": ["agent_id"],
      "properties": {
        "agent_id": { "type": "string" },
        "expected_capabilities": {
          "type": "array",
          "items": { "type": "string" }
        }
      }
    },
    
    "objective": {
      "type": "object",
      "required": ["goal"],
      "properties": {
        "goal": { "type": "string", "maxLength": 500 },
        "acceptance_criteria": {
          "type": "array",
          "items": { "type": "string" },
          "maxItems": 10
        }
      }
    },
    
    "bundle": {
      "type": "object",
      "properties": {
        "progress": {
          "type": "object",
          "properties": {
            "summary": { "type": "string", "maxLength": 1000 },
            "completed_steps": {
              "type": "array",
              "items": { "type": "string" },
              "maxItems": 20
            },
            "current_step": { "type": "string" }
          }
        },
        "decisions": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "decision": { "type": "string" },
              "rationale": { "type": "string" },
              "alternatives_considered": {
                "type": "array",
                "items": { "type": "string" }
              }
            }
          },
          "maxItems": 15
        },
        "artifacts": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "artifact_id": { "type": "string" },
              "name": { "type": "string" },
              "type": { "type": "string" },
              "relevance": { "type": "string", "maxLength": 200 }
            }
          },
          "maxItems": 20
        },
        "memory": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "key": { "type": "string" },
              "summary": { "type": "string", "maxLength": 300 },
              "provenance": { "type": "string" }
            }
          },
          "maxItems": 10
        },
        "open_questions": {
          "type": "array",
          "items": { "type": "string" },
          "maxItems": 10
        },
        "constraints": {
          "type": "object",
          "properties": {
            "must_not_change": {
              "type": "array",
              "items": { "type": "string" }
            },
            "budget_remaining": { "type": "number" },
            "deadline": { "type": "string", "format": "date-time" }
          }
        }
      }
    }
  }
}
```

## Ограничения размера

| Поле | Макс. размер |
|---|---|
| handoff целиком | 64 KB |
| objective.goal | 500 символов |
| progress.summary | 1000 символов |
| decisions | 15 записей |
| artifacts | 20 ссылок |
| memory keys | 10 ключей |

## Пример

```json
{
  "handoff_id": "a1b2c3d4-...",
  "version": "1.0",
  "timestamp": "2026-07-20T12:00:00Z",
  "from_agent": {
    "agent_id": "worker-research",
    "runtime": "hermes",
    "model": "opencode-go/kimi-k2.7-code",
    "run_id": "run-123"
  },
  "to_agent": {
    "agent_id": "worker-code",
    "expected_capabilities": ["terminal", "file", "python"]
  },
  "objective": {
    "goal": "Реализовать EMA-кроссовер стратегию",
    "acceptance_criteria": [
      "Код проходит тесты",
      "Бэктест на Brent > 0% return",
      "Документация в docstring"
    ]
  },
  "bundle": {
    "progress": {
      "summary": "Проанализированы 3 стратегии EMA-кроссовера. Выбран вариант с period=(3,10).",
      "completed_steps": ["Собраны данные Brent", "Протестированы параметры"],
      "current_step": "Реализация на Python"
    },
    "decisions": [{
      "decision": "EMA(3,10) вместо EMA(5,20)",
      "rationale": "Лучше Sharpe на исторических данных",
      "alternatives_considered": ["EMA(5,20)", "SMA(10,30)"]
    }],
    "artifacts": [{
      "artifact_id": "art-001",
      "name": "brent_2024.csv",
      "type": "csv",
      "relevance": "Рыночные данные для бэктеста"
    }],
    "memory": [{
      "key": "brent_seasonality",
      "summary": "Brent показывает сезонный рост Q2-Q3",
      "provenance": "worker-research, run-123"
    }],
    "open_questions": [
      "Учитывать ли спред при расчёте комиссии?"
    ],
    "constraints": {
      "must_not_change": ["сигнатура run_single_pass()"],
      "budget_remaining": 50000
    }
  }
}
```

## Валидация

- schema_version MUST быть "1.0"
- handoff_id MUST быть уникальным
- bundle НЕ должен содержать provider secrets или raw chain-of-thought
- Принимающий агент SHOULD подтвердить получение в течение 30s
