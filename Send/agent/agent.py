import logging
logging.basicConfig(level=logging.DEBUG)
import logging
logging.basicConfig(level=logging.DEBUG)

from fastapi import FastAPI,APIRouter, Header, HTTPException, Request,Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from db.db import get_db
import os,requests

app = FastAPI(title="Orchestration Agent ")

router = APIRouter()

class AgentRegisterReq(BaseModel):
    agent_name: str
    reg_secret: str
    host: Optional[str] = None
    port: Optional[int] = None
    capabilities: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class AgentHeartbeatReq(BaseModel):
    agent_name: str
    status: str = "online"
    metadata: Optional[Dict[str, Any]] = None

def require_admin(x_token: str) -> None:
    db = get_db()
    if not db.validate_token(x_token, required_roles=["admin"]):
        raise HTTPException(status_code=401, detail="invalid admin token")

@router.post("/register")
def register_agent(body: AgentRegisterReq, request: Request):
    reg_secret_env = os.environ.get("AGENT_REG_SECRET")
    if not reg_secret_env or body.reg_secret != reg_secret_env:
        raise HTTPException(status_code=403, detail="invalid reg_secret")

    # Auto-fill host and port
    auto_host = request.client.host
    host = body.host or auto_host
    port = body.port or int(os.environ.get("DEFAULT_AGENT_PORT", 7614))

    db = get_db()
    db.register_or_update_agent(
        agent_name=body.agent_name,
        host=host,
        port=port,
        capabilities=body.capabilities or {},
        metadata=body.metadata or {},
        status="online",
    )
    return {"ok": True, "resolved_host": host, "resolved_port": port}

@router.post("/heartbeat")
def heartbeat(body: AgentHeartbeatReq):
    db = get_db()
    db.heartbeat(
        agent_name=body.agent_name,
        status=body.status,
        metadata=body.metadata or {},
    )
    return {"ok": True}

@app.get("/debug/token")
def debug_token(request: Request):
    return dict(request.headers)

@router.get("/", response_model=List[Dict[str, Any]])
def list_agents(x_admin_token: str = Header(..., alias="X-ADMIN-TOKEN")):
    require_admin(x_admin_token)
    db = get_db()
    return db.list_agents()

app.include_router(router)
