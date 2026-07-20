"""API для получения данных об аккаунтах из 9Router"""
import sqlite3, json
from pathlib import Path
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])

DB_PATH = Path.home() / "AppData/Roaming/9router/db/data.sqlite"

@router.get("")
def get_accounts():
    """Возвращает все аккаунты из 9Router с их статусом"""
    if not DB_PATH.exists():
        return {"accounts": [], "error": "9Router DB not found"}
    
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, provider, authType, name, email, isActive, data, updatedAt "
        "FROM providerConnections ORDER BY provider, priority"
    ).fetchall()
    conn.close()
    
    accounts = []
    for r in rows:
        data = json.loads(r["data"]) if r["data"] else {}
        error_code = data.get("errorCode")
        accounts.append({
            "id": r["id"],
            "provider": r["provider"],
            "auth_type": r["authType"],
            "name": r["name"],
            "email": r["email"],
            "active": bool(r["isActive"]),
            "status": "error" if error_code else ("ok" if data.get("testStatus") != "unavailable" else "unavailable"),
            "error_code": error_code,
            "last_error": data.get("lastError", "")[:100] if data.get("lastError") else None,
            "updated": r["updatedAt"],
        })
    
    return {"accounts": accounts}

@router.get("/provider/{provider}")
def get_provider_accounts(provider: str):
    """Аккаунты конкретного провайдера"""
    if not DB_PATH.exists():
        return {"accounts": [], "error": "9Router DB not found"}
    
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, name, email, isActive, data FROM providerConnections "
        "WHERE provider = ? ORDER BY priority", (provider,)
    ).fetchall()
    conn.close()
    
    accounts = []
    for r in rows:
        data = json.loads(r["data"]) if r["data"] else {}
        error_code = data.get("errorCode")
        backoff = data.get("backoffLevel", 0)
        accounts.append({
            "id": r["id"],
            "name": r["name"],
            "email": r["email"],
            "active": bool(r["isActive"]),
            "ok": not error_code and backoff == 0,
            "error_code": error_code,
            "backoff_level": backoff,
        })
    
    return {"provider": provider, "accounts": accounts, "total_ok": sum(1 for a in accounts if a["ok"])}
