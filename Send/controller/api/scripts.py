from fastapi import APIRouter, Header, HTTPException,Depends
from controller.deps import require_admin

from pydantic import BaseModel
from typing import List, Optional
from controller.db.db import get_db

router = APIRouter(
prefix="/api/scripts",
tags=["scripts"],
dependencies=[Depends(require_admin)]
)


class ScriptCreate(BaseModel):
    script_id: str
    script_file: str
    description: Optional[str] = ""
    allowed_tags: List[str] = []
    required_approval_levels: int = 1

#def require_admin(x_token: str) -> None:
#    db = get_db()
#    if not db.validate_token(x_token, required_roles=["admin"]):
#        raise HTTPException(status_code=401, detail="invalid admin token")

@router.post("/")
def add_script(body: ScriptCreate, ):
    db = get_db()
    db.add_script(
        script_id=body.script_id,
        script_file=body.script_file,
        description=body.description or "",
        allowed_tags=body.allowed_tags,
        required_approval_levels=body.required_approval_levels,
    )
    return {"ok": True}

@router.get("/")
def list_scripts():
    db = get_db()
    return db.list_scripts()

@router.get("/{script_id}")
def get_script(script_id: str, ):
    db = get_db()
    script = db.get_script(script_id)
    if not script:
        raise HTTPException(status_code=404, detail="not found")
    return script
