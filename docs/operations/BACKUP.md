# Backup & Recovery

**Версия:** 0.1.0-draft
**Дата:** 2026-07-20
**Статус:** Draft
**Зависит от:** `SPECIFICATION.md` (§10 Data lifecycle, §7.2 Reliability), `docs/adapters/HERMES.md`

> Этот документ описывает процедуры бэкапа и восстановления конфигурации Hermes Agent в составе Agent Control Center. Реализация запрещена до G0/G1 и утверждения оператором.

## 1. Обзор

Система бэкапа ACC охватывает:
- Конфигурацию Hermes Agent (config.yaml, .env, профили)
- Пользовательские навыки (skills)
- Память (MEMORY.md, USER.md)
- Сессионные данные (опционально)

Бэкап НЕ включает:
- Секреты (API-ключи) — управляются отдельно через secret manager
- Бинарные артефакты и кэши (audio_cache, сессионные файлы)
- Логи (сохраняются согласно retention policy)

## 2. Структура конфигурации Hermes

### 2.1 Основные компоненты

```
~/.hermes/
├── config.yaml              # Основная конфигурация
├── .env                     # Переменные окружения (API-ключи, секреты)
├── auth.json                # OAuth-токены и credential pools
├── state.db                 # SQLite база сессий (state store)
├── profiles/                # Профили
│   ├── default/
│   │   ├── config.yaml
│   │   ├── .env
│   │   ├── skills/
│   │   └── memories/
│   ├── worker-code/
│   │   └── ...
│   ├── worker-fast/
│   │   └── ...
│   ├── worker-research/
│   │   └── ...
│   └── worker-review/
│       └── ...
├── skills/                  # Пользовательские навыки
│   ├── *.md                 # SKILL.md файлы
│   └── .usage.json          # Метаданные curator'а
├── sessions/                # Сессионные файлы (опционально)
├── logs/                    # Логи (НЕ бэкапируются)
├── audio_cache/             # Аудиокэш (НЕ бэкапируется)
└── backups/                 # Локальные снапшоты
    ├── latest/              # Последний снапшот
    │   ├── config.yaml
    │   ├── config.yaml.sig
    │   └── manifest.json
    └── archive/             # Архив снапшотов
        └── 2026-07-20T14-00-00Z.tar.gz
```

### 2.2 Приоритеты бэкапа

| Компонент | Приоритет | RPO | Без секретов |
|---|---|---|---|
| `config.yaml` (все профили) | CRITICAL | 1 час | Да |
| `skills/` | HIGH | 6 часов | Да |
| `memories/` (MEMORY.md, USER.md) | HIGH | 6 часов | Да |
| `profiles/*/config.yaml` | HIGH | 1 час | Да |
| `cron/` конфигурации | MEDIUM | 24 часа | Да |
| `sessions/` | LOW | 24 часа | Нет (секреты в сессиях) |
| `state.db` | LOW | 24 часа | Нет |

## 3. Процедура снапшота

### 3.1 Скрипт: `scripts/update_backup.py`

```python
#!/usr/bin/env python3
"""
update_backup.py — создание снапшота конфигурации Hermes Agent.

Использование:
    python scripts/update_backup.py [--output DIR] [--exclude-secrets] [--dry-run]

Снапшот включает:
    - config.yaml всех профилей
    - .env (с redacted секретами при --exclude-secrets)
    - skills/ (только SKILL.md файлы)
    - memories/ (MEMORY.md, USER.md)
    - cron/ конфигурации

Исключает:
    - sessions/
    - logs/
    - audio_cache/
    - state.db (опционально)
    - auth.json (секреты)
"""

import os
import json
import shutil
import tarfile
import hashlib
from datetime import datetime, timezone
from pathlib import Path

HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
BACKUP_DIR = HERMES_HOME / "backups"
LATEST_DIR = BACKUP_DIR / "latest"
ARCHIVE_DIR = BACKUP_DIR / "archive"

# Директории для бэкапа
INCLUDE_DIRS = [
    HERMES_HOME / "skills",
    HERMES_HOME / "profiles",
]

# Файлы для бэкапа
INCLUDE_FILES = [
    HERMES_HOME / "config.yaml",
    HERMES_HOME / ".env",
]

# Директории для исключения
EXCLUDE_PATTERNS = [
    "**/sessions/",
    "**/logs/",
    "**/audio_cache/",
    "**/state.db",
    "**/auth.json",
    "**/__pycache__/",
    "**/*.pyc",
]

def create_snapshot(output_dir: Path, exclude_secrets: bool = False):
    """Создать снапшот конфигурации."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    snapshot_dir = output_dir / timestamp

    snapshot_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "version": "0.1.0",
        "created_at": timestamp,
        "hermes_home": str(HERMES_HOME),
        "files": [],
        "exclude_secrets": exclude_secrets,
    }

    # Копирование конфигурационных файлов
    for src in INCLUDE_FILES:
        if src.exists():
            dst = snapshot_dir / src.relative_to(HERMES_HOME)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

            # Redact секреты в .env если нужно
            if exclude_secrets and dst.name == ".env":
                redact_env_secrets(dst)

            file_hash = hash_file(dst)
            manifest["files"].append({
                "path": str(src.relative_to(HERMES_HOME)),
                "hash": file_hash,
                "size": dst.stat().st_size,
            })

    # Копирование директорий с исключениями
    for src_dir in INCLUDE_DIRS:
        if src_dir.exists() and src_dir.is_dir():
            _copy_with_exclusions(
                src_dir,
                snapshot_dir / src_dir.relative_to(HERMES_HOME),
                manifest,
            )

    # Сохранение манифеста
    manifest_path = snapshot_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))

    # Обновление симлинка latest
    if LATEST_DIR.exists():
        if LATEST_DIR.is_symlink():
            LATEST_DIR.unlink()
        else:
            shutil.rmtree(LATEST_DIR)
    os.symlink(snapshot_dir, LATEST_DIR, target_is_directory=True)

    # Создание архива
    archive_path = ARCHIVE_DIR / f"{timestamp}.tar.gz"
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(snapshot_dir, arcname=timestamp)

    print(f"Snapshot created: {snapshot_dir}")
    print(f"Archive: {archive_path}")
    print(f"Manifest: {len(manifest['files'])} files")

    # Очистка старых архивов (> 30 дней)
    cleanup_old_archives(days=30)

def redact_env_secrets(env_path: Path):
    """Заменить значения секретов на REDACTED."""
    content = env_path.read_text()
    redacted_lines = []
    for line in content.split("\n"):
        if "=" in line and not line.startswith("#"):
            key, _ = line.split("=", 1)
            if any(s in key.upper() for s in ["KEY", "TOKEN", "SECRET", "PASSWORD"]):
                redacted_lines.append(f"{key}=REDACTED")
            else:
                redacted_lines.append(line)
        else:
            redacted_lines.append(line)
    env_path.write_text("\n".join(redacted_lines))

def hash_file(path: Path) -> str:
    """SHA-256 хеш файла."""
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha.update(chunk)
    return sha.hexdigest()

def cleanup_old_archives(days: int = 30):
    """Удалить архивы старше N дней."""
    cutoff = datetime.now(timezone.utc).timestamp() - days * 86400
    for archive in ARCHIVE_DIR.glob("*.tar.gz"):
        if archive.stat().st_mtime < cutoff:
            archive.unlink()
            print(f"Removed old archive: {archive.name}")


def _copy_with_exclusions(src: Path, dst: Path, manifest: dict):
    """Копировать директорию с исключениями."""
    from fnmatch import fnmatch

    for root, dirs, files in os.walk(src):
        root_path = Path(root)

        # Пропустить исключённые директории
        dirs[:] = [
            d for d in dirs
            if not any(fnmatch(str(root_path / d), pat) for pat in EXCLUDE_PATTERNS)
        ]

        for fname in files:
            fpath = root_path / fname
            if any(fnmatch(str(fpath), pat) for pat in EXCLUDE_PATTERNS):
                continue

            rel = fpath.relative_to(HERMES_HOME)
            dest = dst / rel.relative_to(src)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(fpath, dest)

            file_hash = hash_file(dest)
            manifest["files"].append({
                "path": str(rel),
                "hash": file_hash,
                "size": dest.stat().st_size,
            })


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Hermes config snapshot")
    parser.add_argument("--output", type=Path, default=BACKUP_DIR,
                        help="Output directory")
    parser.add_argument("--exclude-secrets", action="store_true",
                        help="Redact secrets in .env files")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be backed up, without copying")
    args = parser.parse_args()

    if args.dry_run:
        print("Files to backup:")
        for f in INCLUDE_FILES:
            if f.exists():
                print(f"  {f}")
        for d in INCLUDE_DIRS:
            if d.exists():
                print(f"  {d}/")
    else:
        create_snapshot(args.output, exclude_secrets=args.exclude_secrets)
```

### 3.2 Ручной снапшот

```bash
# Стандартный снапшот
python scripts/update_backup.py

# Снапшот с redacted секретами (для хранения в Git)
python scripts/update_backup.py --exclude-secrets

# Предварительный просмотр
python scripts/update_backup.py --dry-run

# В указанную директорию
python scripts/update_backup.py --output /mnt/backups/hermes/
```

### 3.3 Автоматизация через cron

```bash
# Добавить задание в crontab
# Ежечасный снапшот с исключением секретов
0 * * * * cd ~/acc-local && python scripts/update_backup.py --exclude-secrets --output ~/.hermes/backups/

# Ежедневный полный снапшот
0 2 * * * cd ~/acc-local && python scripts/update_backup.py --output ~/.hermes/backups/
```

## 4. Процедура восстановления

### 4.1 Скрипт: `scripts/restore_backup.py`

```python
#!/usr/bin/env python3
"""
restore_backup.py — восстановление конфигурации Hermes Agent из снапшота.

Использование:
    python scripts/restore_backup.py --snapshot DIR
    python scripts/restore_backup.py --latest
    python scripts/restore_backup.py --list
    python scripts/restore_backup.py --verify DIR
"""

import os
import json
import shutil
import hashlib
from pathlib import Path
from datetime import datetime, timezone

HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
BACKUP_DIR = HERMES_HOME / "backups"
LATEST_DIR = BACKUP_DIR / "latest"
ARCHIVE_DIR = BACKUP_DIR / "archive"
RESTORE_DIR = HERMES_HOME / "restore_tmp"


def list_snapshots():
    """Показать доступные снапшоты."""
    if not ARCHIVE_DIR.exists():
        print("No archives found.")
        return

    archives = sorted(ARCHIVE_DIR.glob("*.tar.gz"), reverse=True)
    for i, arc in enumerate(archives):
        size_mb = arc.stat().st_size / (1024 * 1024)
        mtime = datetime.fromtimestamp(arc.stat().st_mtime)
        print(f"  [{i}] {arc.name}  {size_mb:.1f} MB  {mtime.isoformat()}")


def verify_snapshot(snapshot_dir: Path):
    """Проверить целостность снапшота."""
    manifest_path = snapshot_dir / "manifest.json"
    if not manifest_path.exists():
        print("ERROR: manifest.json not found")
        return False

    manifest = json.loads(manifest_path.read_text())
    all_ok = True

    for fspec in manifest.get("files", []):
        fpath = snapshot_dir / fspec["path"]
        if not fpath.exists():
            print(f"  MISSING: {fspec['path']}")
            all_ok = False
            continue

        actual_hash = hashlib.sha256(fpath.read_bytes()).hexdigest()
        if actual_hash != fspec["hash"]:
            print(f"  HASH MISMATCH: {fspec['path']}")
            all_ok = False

    if all_ok:
        print(f"VERIFIED: {len(manifest['files'])} files OK")
    return all_ok


def restore_snapshot(snapshot_dir: Path, dry_run: bool = False):
    """Восстановить конфигурацию из снапшота."""
    manifest_path = snapshot_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text())

    print(f"Restoring from: {snapshot_dir}")
    print(f"Created: {manifest.get('created_at', 'unknown')}")
    print(f"Files: {len(manifest['files'])}")
    print(f"{'[DRY RUN] ' if dry_run else ''}")

    conflicts = []

    for fspec in manifest.get("files", []):
        src = snapshot_dir / fspec["path"]
        dst = HERMES_HOME / fspec["path"]

        if not src.exists():
            print(f"  SKIP (missing): {fspec['path']}")
            continue

        # Проверить конфликт
        if dst.exists() and not dry_run:
            dst_hash = hashlib.sha256(dst.read_bytes()).hexdigest()
            if dst_hash != fspec["hash"]:
                conflicts.append(fspec["path"])

        if dry_run:
            action = "CONFLICT" if dst.exists() else "CREATE"
            print(f"  [{action}] {fspec['path']}")
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"  RESTORED: {fspec['path']}")

    if conflicts:
        print(f"\nWARNING: {len(conflicts)} files had local modifications (overwritten):")
        for p in conflicts:
            print(f"  - {p}")

    if dry_run:
        print(f"\nDry run complete. {len(manifest['files'])} files would be restored.")

    print("Restore complete.")
    print("NOTE: .env files were backed up with redacted secrets.")
    print("      Manually restore API keys and secrets after restore.")


def restore_from_archive(archive_path: Path):
    """Восстановить из tar.gz архива."""
    import tarfile

    extract_dir = RESTORE_DIR / archive_path.stem
    extract_dir.mkdir(parents=True, exist_ok=True)

    with tarfile.open(archive_path, "r:gz") as tar:
        tar.extractall(extract_dir)

    # Найти директорию снапшота внутри архива
    snapshots = list(extract_dir.glob("*/manifest.json"))
    if not snapshots:
        print("ERROR: No manifest.json found in archive")
        return

    snapshot_dir = snapshots[0].parent
    restore_snapshot(snapshot_dir)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Hermes config restore")
    parser.add_argument("--snapshot", type=Path,
                        help="Snapshot directory to restore from")
    parser.add_argument("--latest", action="store_true",
                        help="Restore from latest snapshot")
    parser.add_argument("--list", action="store_true",
                        help="List available snapshots")
    parser.add_argument("--verify", type=Path,
                        help="Verify snapshot integrity")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be restored")
    args = parser.parse_args()

    if args.list:
        list_snapshots()
    elif args.verify:
        verify_snapshot(Path(args.verify))
    elif args.latest:
        if not LATEST_DIR.exists():
            print("ERROR: No latest snapshot found")
            exit(1)
        if args.dry_run:
            restore_snapshot(LATEST_DIR, dry_run=True)
        else:
            verify_snapshot(LATEST_DIR)
            restore_snapshot(LATEST_DIR)
    elif args.snapshot:
        snapshot = Path(args.snapshot)
        if snapshot.suffix == ".gz":
            restore_from_archive(snapshot)
        else:
            if args.dry_run:
                restore_snapshot(snapshot, dry_run=True)
            else:
                verify_snapshot(snapshot)
                restore_snapshot(snapshot)
    else:
        parser.print_help()
```

### 4.2 Ручное восстановление

```bash
# Список доступных снапшотов
python scripts/restore_backup.py --list

# Восстановить последний снапшот
python scripts/restore_backup.py --latest

# Восстановить конкретный снапшот
python scripts/restore_backup.py --snapshot ~/.hermes/backups/2026-07-20T14-00-00Z

# Восстановить из архива
python scripts/restore_backup.py --snapshot ~/.hermes/backups/archive/2026-07-20T14-00-00Z.tar.gz

# Проверить целостность без восстановления
python scripts/restore_backup.py --verify ~/.hermes/backups/latest

# Предварительный просмотр
python scripts/restore_backup.py --latest --dry-run
```

## 5. Git-репозиторий как хранилище

### 5.1 Структура репозитория `ochenstarik-ui/hermes-config-backup`

```
hermes-config-backup/
├── README.md
├── config/
│   ├── default.yaml           # Без секретов
│   ├── worker-code.yaml
│   ├── worker-fast.yaml
│   ├── worker-research.yaml
│   └── worker-review.yaml
├── skills/                    # Пользовательские навыки
│   └── *.md
├── memories/                  # Память (без чувствительных данных)
│   ├── MEMORY.md
│   └── USER.md
├── scripts/
│   ├── update_backup.py
│   ├── restore_backup.py
│   └── sync_to_git.sh
└── .gitignore
```

### 5.2 `.gitignore`

```gitignore
# Исключить файлы с секретами
.env
*.env
auth.json
credentials/
secrets/

# Исключить чувствительные данные сессий
sessions/
state.db

# Исключить временные файлы
*.pyc
__pycache__/
backups/archive/
backups/latest/
```

### 5.3 Синхронизация: `scripts/sync_to_git.sh`

```bash
#!/bin/bash
# sync_to_git.sh — синхронизация снапшота в Git-репозиторий

set -euo pipefail

REPO_DIR="$HOME/hermes-config-backup"
SNAPSHOT_DIR="$HOME/.hermes/backups/latest"

cd "$REPO_DIR"

# Копировать файлы из снапшота (без секретов)
if [ -d "$SNAPSHOT_DIR" ]; then
    # config.yaml профилей
    cp "$SNAPSHOT_DIR/config.yaml" config/default.yaml 2>/dev/null || true
    cp "$SNAPSHOT_DIR/profiles/worker-code/config.yaml" config/worker-code.yaml 2>/dev/null || true
    cp "$SNAPSHOT_DIR/profiles/worker-fast/config.yaml" config/worker-fast.yaml 2>/dev/null || true
    cp "$SNAPSHOT_DIR/profiles/worker-research/config.yaml" config/worker-research.yaml 2>/dev/null || true
    cp "$SNAPSHOT_DIR/profiles/worker-review/config.yaml" config/worker-review.yaml 2>/dev/null || true

    # Навыки
    rm -rf skills/
    cp -r "$SNAPSHOT_DIR/skills/" skills/ 2>/dev/null || true

    # Память
    mkdir -p memories/
    cp "$SNAPSHOT_DIR/profiles/default/memories/MEMORY.md" memories/ 2>/dev/null || true
    cp "$SNAPSHOT_DIR/profiles/default/memories/USER.md" memories/ 2>/dev/null || true
fi

# Commit и push
git add -A
if git diff --cached --quiet; then
    echo "No changes to commit."
else
    git commit -m "backup: $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
    git push origin main
    echo "Backup synced to GitHub."
fi
```

## 6. Исключение секретов

| Компонент | Статус секретов | Действие при бэкапе |
|---|---|---|
| `config.yaml` | Может содержать `api_key` references | Проверить на прямые ключи; использовать `${ENV_VAR}` синтаксис |
| `.env` | Содержит API-ключи | REDACT при `--exclude-secrets`; NEVER commit в Git |
| `auth.json` | OAuth-токены | Исключён из бэкапа полностью |
| `state.db` | Может содержать ключи в сессиях | Исключён из бэкапа |
| `skills/` | Обычно без секретов | Бэкапируется; проверить на embedded ключи |
| `memories/` | Может содержать косвенные ссылки | Бэкапируется; проверить на чувствительные данные |

### 6.1 Проверка на секреты перед commit

```bash
# Проверить снапшот на наличие паттернов секретов
grep -rE "(sk-|api_key|token|secret|password|-----BEGIN)" ~/.hermes/backups/latest/ \
  --exclude-dir=sessions --exclude="*.pyc" && echo "WARNING: Potential secrets found!"
```

## 7. Процедуры

### 7.1 Плановый бэкап (ежедневно)

```bash
#!/bin/bash
# daily_backup.sh

echo "=== Daily backup $(date) ==="

# 1. Создать снапшот
python scripts/update_backup.py --exclude-secrets
echo "Snapshot created."

# 2. Проверить целостность
python scripts/restore_backup.py --verify ~/.hermes/backups/latest
echo "Integrity verified."

# 3. Синхронизировать в Git
bash scripts/sync_to_git.sh
echo "Git sync complete."

# 4. Очистить старые архивы (> 30 дней)
find ~/.hermes/backups/archive/ -name "*.tar.gz" -mtime +30 -delete
echo "Old archives cleaned."
```

### 7.2 Восстановление после сбоя

```bash
#!/bin/bash
# disaster_recovery.sh

echo "=== Disaster Recovery $(date) ==="
echo "WARNING: This will overwrite current Hermes configuration!"
read -p "Continue? (yes/no): " confirm
[[ "$confirm" != "yes" ]] && exit 0

# 1. Создать аварийный снапшот текущего состояния
python scripts/update_backup.py --output ~/.hermes/backups/pre_recovery
echo "Pre-recovery snapshot created."

# 2. Восстановить из последнего снапшота
python scripts/restore_backup.py --latest
echo "Config restored."

# 3. Проверить конфигурацию
hermes config check
echo "Config check complete."

# 4. Проверить health
hermes doctor
echo "Health check complete."

# 5. Перезапустить gateway
hermes gateway restart
echo "Gateway restarted."

echo "=== Recovery complete ==="
echo "NOTE: API keys (.env) were redacted in backup."
echo "      Manually restore API keys if needed."
```

## 8. RPO и RTO

| Сценарий | RPO | RTO | Процедура |
|---|---|---|---|
| Повреждение `config.yaml` | ≤ 1 час | ≤ 5 мин | `restore_backup.py --latest` |
| Потеря навыков | ≤ 6 часов | ≤ 10 мин | `restore_backup.py --latest` |
| Полная потеря `~/.hermes/` | ≤ 1 час (config) / ≤ 24 часа (sessions) | ≤ 30 мин | `disaster_recovery.sh` |
| Миграция на новый сервер | ≤ 1 час | ≤ 1 час | Клонировать Git-репозиторий + восстановить секреты |

## 9. Ссылки

- [HERMES.md](../adapters/HERMES.md) — спецификация Hermes-адаптера (конфигурация)
- [MONITORING.md](MONITORING.md) — мониторинг и алерты (включая ALT-BKP-001)
- [CREDENTIAL_POOLS.md](../patterns/CREDENTIAL_POOLS.md) — управление ключами
- [SPECIFICATION.md](../SPECIFICATION.md) §10 — Data lifecycle
- [SPECIFICATION.md](../SPECIFICATION.md) §7.2 — Reliability, consistency and recovery
