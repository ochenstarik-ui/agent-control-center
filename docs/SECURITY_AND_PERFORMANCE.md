# Security & Performance

**Версия:** 0.1.0-draft | **Статус:** Draft

## 1. Security

### 1.1 Ротация секретов

| Секрет | Период ротации | Автоматически |
|---|---|---|
| Connector mTLS cert | 90 дней | ✅ (ACME/внутренний CA) |
| API signing keys | 30 дней | ✅ |
| OAuth refresh tokens | По истечению | ✅ (провайдер) |
| User sessions | 24 часа | ✅ (JWT expiry) |
| API keys (provider) | Вручную | ❌ |

### 1.2 Управление ключами

- **Иерархия:** Root CA → Intermediate CA → Connector cert
- **Хранение:** Vault/HSM для production; зашифрованный файл для dev
- **Доступ:** Только Connector Gateway (machine identity)
- **Отзыв:** CRL + OCSP, задержка распространения ≤ 5 минут

### 1.3 Шифрование

| Уровень | Метод |
|---|---|
| Transport | TLS 1.3 (min) |
| Data at rest | AES-256-GCM (Object Storage, DB) |
| Secrets | Vault transit engine |
| Backups | GPG (асимметричное, offline-ключ) |

### 1.4 Аудит

- Все события → append-only audit log
- Защита от удаления/модификации: WORM storage (30 дней min)
- Экспорт: CSV/JSON, фильтрация по actor, target, time range
- Критические события: real-time alert (connector offline, mass approval deny)

### 1.5 Отзыв коннекторов

- **Немедленный:** Revoke cert → disconnect active WSS → block re-registration
- **Плановый:** Deprecation notice (7 дней) → revoke → cleanup
- **Аварийный:** One-click kill switch (Operator/Admin role)

### 1.6 Резервное копирование

- Конфигурация: Git-репо (hermes-config-backup паттерн)
- Базы данных: ежедневно, retention 30 дней
- Проверка восстановления: ежемесячно (automated restore test)

## 2. Performance Targets

### 2.1 Нагрузка MVP

| Параметр | Значение |
|---|---|
| Simultaneous users | 5 (MVP), 50 (M5) |
| Active connectors | 3 (MVP), 20 (M5) |
| Concurrent runs | 10 (MVP), 100 (M5) |
| Events/sec | 5 (MVP), 50 (M5) |
| Total artifacts | 1 000 (MVP), 100 000 (M5) |
| Wiki pages | 100 (MVP), 10 000 (M5) |
| Memory entries | 1 000 (MVP), 100 000 (M5) |

### 2.2 Latency Budget

| Компонент | Бюджет (p95) |
|---|---|
| API Gateway | 50ms |
| Auth (JWT verify) | 10ms |
| DB query (read) | 20ms |
| DB query (write) | 50ms |
| Object Storage | 100ms |
| Event Bus publish | 30ms |
| **Total REST read** | **≤ 200ms** |
| **Total REST write** | **≤ 500ms** |

### 2.3 Throughput

| Операция | Цель |
|---|---|
| REST API req/sec | 100 (однопоточный) |
| WSS connections | 50 одновременных |
| Event delivery | 100 events/sec |
| Search queries | 20 QPS |

### 2.4 Capacity Planning

| Ресурс | Min (MVP) | Recommended |
|---|---|---|
| CPU | 2 cores | 4 cores |
| RAM | 4 GB | 8 GB |
| Disk | 20 GB SSD | 100 GB SSD |
| Network | 100 Mbps | 1 Gbps |
