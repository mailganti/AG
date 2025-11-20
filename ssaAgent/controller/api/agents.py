from fastapi import APIRouter, HTTPException, Request, Depends
from controller.deps import require_admin
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os

from controller.db.db import get_db

router = APIRouter(
    prefix="/api/agents",
    tags=["agents"],
    dependencies=[Depends(require_admin)]   # GLOBAL AUTH ENFORCEMENT
)

# ============================
#  SCHEMAS
# ============================

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


# ============================
#  ROUTES
# ============================

@router.post("/register/")
def register_agent(body: AgentRegisterReq, request: Request):
    reg_secret_env = os.environ.get("AGENT_REG_SECRET")
    if not reg_secret_env or body.reg_secret != reg_secret_env:
        raise HTTPException(status_code=403, detail="invalid_reg_secret")

    client_host = request.client.host
    resolved_host = body.host or client_host

    default_port = int(os.environ.get("DEFAULT_AGENT_PORT", 7614))
    resolved_port = body.port or default_port

    db = get_db()
    db.register_or_update_agent(
        agent_name=body.agent_name,
        host=resolved_host,
        port=resolved_port,
        capabilities=body.capabilities or {},
        metadata=body.metadata or {},
        status="online",
    )

    return {
        "ok": True,
        "resolved_host": resolved_host,
        "resolved_port": resolved_port
    }


@router.post("/heartbeat/")
def heartbeat(body: AgentHeartbeatReq):
    db = get_db()
    db.heartbeat(
        agent_name=body.agent_name,
        status=body.status,
        metadata=body.metadata or {},
    )
    return {"ok": True}


@router.get("/", response_model=List[Dict[str, Any]])
def list_agents():
    db = get_db()
    return db.list_agents()
