from fastapi import FastAPI,APIRouter, Header, HTTPException, Request,Depends
from controller.depends import require_admin
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os

from controller.db.db import get_db   # adjust if your db path is different

agents_router = APIRouter()

router = APIRouter(
prefix="/agents",
tags=["agents"],
dependencies=[Depends(require_admin)]
)


# ============================
#  SCHEMAS
# ============================

class AgentRegister(BaseModel):
    agent_name: str
    hostname: str
    port: int
    metadata: dict = {}
    reg_secret: str

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



from fastapi import HTTPException, Header
import os

@agents_router.get("/")
async def get_agents(x_admin_token: str = Header(...)):
    print("=== AGENTS API DEBUG ===")
    print(f"Header received: x_admin_token = '{x_admin_token}'")
    print(f"ADMIN_TOKEN env var: '{os.environ.get('ADMIN_TOKEN')}'")
    
    expected_token = os.environ.get("ADMIN_TOKEN")
    if not expected_token:
        print("❌ ADMIN_TOKEN environment variable is not set!")
        raise HTTPException(status_code=500, detail="Server configuration error")
    
    if x_admin_token != expected_token:
        print(f"❌ Token mismatch! Expected: '{expected_token}', Got: '{x_admin_token}'")
        raise HTTPException(status_code=401, detail="Invalid admin token")
    
    print("✅ Token validation successful!")
    
    # Return simple test data
    return {
        "message": "success", 
        "data": [
            {
                "agent_name": "test-agent-1", 
                "hostname": "localhost", 
                "port": 8080, 
                "status": "online", 
                "last_seen": "2023-01-01"
            }
        ]
    }

# ============================
#  HELPERS
# ============================

def require_admin(x_token: str) -> None:
    db = get_db()
    if not db.validate_token(x_token, required_roles=["admin"]):
        raise HTTPException(status_code=401, detail="invalid admin token")


# ============================
#  ROUTES
# ============================

@router.post("/register")
def register_agent(body: AgentRegisterReq, request: Request):
    """
    Register new agent or update existing record.
    Host + port are optional.
    Host is auto-detected from request IP.
    Port defaults to DEFAULT_AGENT_PORT or 7614.
    """

    reg_secret_env = os.environ.get("AGENT_REG_SECRET")
    if not reg_secret_env or body.reg_secret != reg_secret_env:
        raise HTTPException(status_code=403, detail="invalid reg_secret")

    # Auto-detect host if missing
    client_host = request.client.host
    resolved_host = body.host or client_host

    # Default port (fallback to env or default 7614)
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


@router.post("/heartbeat")
def heartbeat(body: AgentHeartbeatReq):
    """
    Update agent heartbeat timestamp + status.
    """
    db = get_db()
    db.heartbeat(
        agent_name=body.agent_name,
        status=body.status,
        metadata=body.metadata or {},
    )
    return {"ok": True}


@router.get("/", response_model=List[Dict[str, Any]])
def list_agents(x_admin_token: str = Header(..., alias="x_admin_token")):
    """
    List all agents (admin authentication required).
    """
    require_admin(x_admin_token)
    db = get_db()
    return db.list_agents()
