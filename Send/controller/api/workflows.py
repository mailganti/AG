import secrets, datetime, json, os, subprocess
from controller.deps import require_admin

from fastapi import APIRouter, Header, HTTPException,Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from controller.db.db import get_db

router = APIRouter(
prefix="/api/workflows",
tags=["workflow"],
dependencies=[Depends(require_admin)]
)



class WorkflowCreate(BaseModel):
    script_id: str
    targets: List[str]
    required_approval_levels: int = 1
    notify_email: Optional[str] = None
    ttl_minutes: int = 60
    reason: str
    requestor: str

class WorkflowApprove(BaseModel):
    note: Optional[str] = ""

def require_role(x_token: str, roles: List[str]) -> str:
    db = get_db()
    if not db.validate_token(x_token, required_roles=roles):
        raise HTTPException(status_code=401, detail="invalid token")
    return "token-user"

@router.post("/")
def create_workflow(body: WorkflowCreate, ):
    require_role(x_admin_token , ["admin", "requestor"])
    db = get_db()
    script = db.get_script(body.script_id)
    if not script:
        raise HTTPException(status_code=400, detail="unknown script_id")
    wid = secrets.token_urlsafe(16)
    db.create_workflow(
        workflow_id=wid,
        script_id=body.script_id,
        targets=body.targets,
        requestor=body.requestor,
        required_levels=body.required_approval_levels,
        notify_email=body.notify_email or "",
        ttl_minutes=body.ttl_minutes,
        reason=body.reason,
    )
    db.add_audit(wid, "created", body.requestor, note=body.reason)
    return {"workflow_id": wid}

@router.get("/")
def list_workflows(limit: int = 100, ):
    require_role(x_admin_token, ["admin", "approver", "viewer"])
    db = get_db()
    return db.list_workflows(limit)

@router.get("/{workflow_id}")
def get_workflow(workflow_id: str, ):
    require_role(x_admin_token, ["admin", "approver", "viewer"])
    db = get_db()
    wf = db.get_workflow(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="not found")
    return wf

@router.get("/{workflow_id}/audit")
def get_audit(workflow_id: str, ):
    require_role(x_admin_token , ["admin", "approver", "viewer"])
    db = get_db()
    return {"audit": db.get_audit(workflow_id)}

@router.post("/{workflow_id}/approve")
def approve_workflow(workflow_id: str, body: WorkflowApprove, ):
    actor = require_role(x_admin_token, ["admin", "approver"])
    db = get_db()
    wf = db.get_workflow(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="not found")
    if wf["status"] not in ("pending", "approved"):
        raise HTTPException(status_code=400, detail=f"cannot approve in status {wf['status']}")
    db.add_approval(workflow_id, actor, 1)
    db.add_audit(workflow_id, "approved", actor, note=body.note or "")
    wf = db.get_workflow(workflow_id)
    approvals = len(json.loads(wf.get("approvals_json") or "[]"))
    if approvals >= int(wf["required_approval_levels"] or 1):
        db.update_workflow_status(workflow_id, "approved")
    return {"ok": True, "approvals": approvals}

@router.post("/{workflow_id}/deny")
def deny_workflow(workflow_id: str, body: WorkflowApprove, ):
    actor = require_role(x_admin_token, ["admin", "approver"])
    db = get_db()
    wf = db.get_workflow(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="not found")
    if wf["status"] not in ("pending", "approved"):
        raise HTTPException(status_code=400, detail=f"cannot deny in status {wf['status']}")
    db.update_workflow_status(workflow_id, "denied")
    db.add_audit(workflow_id, "denied", actor, note=body.note or "")
    return {"ok": True}

@router.post("/{workflow_id}/execute")
def execute_workflow(workflow_id: str, ):
    actor = require_role(x_admin_token, ["admin"])
    db = get_db()
    wf = db.get_workflow(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="not found")
    if wf["status"] != "approved":
        raise HTTPException(status_code=400, detail="workflow not approved")
    now = datetime.datetime.utcnow().isoformat() + "Z"
    if wf.get("expires_at") and now > wf["expires_at"]:
        db.update_workflow_status(workflow_id, "expired")
        db.add_audit(workflow_id, "expired", actor, note="TTL expired")
        raise HTTPException(status_code=400, detail="workflow expired")
    script = db.get_script(wf["script_id"])
    if not script:
        raise HTTPException(status_code=400, detail="script not found")
    script_path = script["script_file"]
    if not os.path.isabs(script_path):
        script_path = os.path.join(os.getcwd(), script_path)
    try:
        result = subprocess.run(
            [script_path],
            capture_output=True,
            text=True,
            check=False,
        )
        status = "success" if result.returncode == 0 else "failed"
    except Exception as e:
        status = "failed"
        result = type("Obj", (), {"returncode": -1, "stdout": "", "stderr": str(e)})
    db.update_workflow_status(workflow_id, status)
    db.add_audit(workflow_id, "executed", actor, note=f"rc={result.returncode}")
    targets = json.loads(wf.get("targets_json") or "[]")
    return {
        "status": status,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "targets": targets,
    }
