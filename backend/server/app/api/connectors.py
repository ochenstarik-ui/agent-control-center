"""OAuth коннекторы — GitHub, Gmail, Google Drive, Yandex Disk, Google Calendar"""
from __future__ import annotations
import secrets, json
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/connectors", tags=["connectors"])

# In-memory OAuth state store (заменить на БД в production)
_pending: dict[str, dict] = {}
_connections: dict[str, list[dict]] = {}

OAUTH_CONFIG = {
    "github": {
        "name": "GitHub",
        "auth_url": "https://github.com/login/oauth/authorize",
        "scope": "repo,user",
    },
    "gmail": {
        "name": "Gmail",
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "scope": "https://www.googleapis.com/auth/gmail.readonly",
    },
    "gdrive": {
        "name": "Google Drive",
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "scope": "https://www.googleapis.com/auth/drive.readonly",
    },
    "gcal": {
        "name": "Google Calendar",
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "scope": "https://www.googleapis.com/auth/calendar.readonly",
    },
    "ydisk": {
        "name": "Yandex Disk",
        "auth_url": "https://oauth.yandex.ru/authorize",
        "scope": "cloud_api:disk.read",
    },
}

class OAuthInitRequest(BaseModel):
    provider: str
    project_id: str

@router.post("/oauth/init")
def oauth_init(req: OAuthInitRequest):
    if req.provider not in OAUTH_CONFIG:
        return {"error": "unknown_provider"}
    
    cfg = OAUTH_CONFIG[req.provider]
    state = secrets.token_urlsafe(16)
    _pending[state] = {"provider": req.provider, "project_id": req.project_id}
    
    # В production здесь формируется полный URL с client_id и redirect_uri
    client_id = "ACC_CLIENT_ID_PLACEHOLDER"
    redirect_uri = "http://localhost:8100/api/v1/connectors/oauth/callback"
    auth_url = f"{cfg['auth_url']}?client_id={client_id}&redirect_uri={redirect_uri}&scope={cfg['scope']}&state={state}&response_type=code"
    
    return {"auth_url": auth_url, "state": state, "provider": req.provider}

@router.get("/oauth/callback")
def oauth_callback(code: str, state: str):
    """OAuth callback — обработка кода авторизации"""
    if state not in _pending:
        return {"error": "invalid_state"}
    
    pending = _pending.pop(state)
    provider = pending["provider"]
    
    # В production: обменять code на access_token через POST к token endpoint
    connection = {
        "provider": provider,
        "account": f"{provider}_user",
        "label": OAUTH_CONFIG[provider]["name"],
        "token_valid": True,
        "state": state,
    }
    
    if pending["project_id"] not in _connections:
        _connections[pending["project_id"]] = []
    _connections[pending["project_id"]].append(connection)
    
    return {"connected": True, "provider": provider, **connection}

@router.get("/oauth/check")
def oauth_check(state: str):
    """Проверка статуса OAuth-авторизации (polling)"""
    if state in _pending:
        return {"connected": False, "status": "pending"}
    
    # Найти connection по state
    for conns in _connections.values():
        for c in conns:
            if c.get("state") == state:
                return {"connected": True, **c}
    
    return {"connected": False, "status": "expired"}
