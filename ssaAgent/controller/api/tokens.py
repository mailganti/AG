from fastapi import APIRouter, Header, HTTPException,Depends
from controller.deps import require_admin


from pydantic import BaseModel
from typing import List, Optional
from controller.db.db import get_db

router = APIRouter(
prefix="/api/tokens",
tags=["tokens"],
dependencies=[Depends(require_admin)]
)



class TokenCreate(BaseModel):
    token_name: str
    role: str
    description: Optional[str] = ""

class TokenOut(BaseModel):
    token_name: str
    role: str
    description: Optional[str]
    created_at: Optional[str]
    revoked: bool


@router.post("/", response_model=str)
def create_token(body: TokenCreate, ):
    import secrets
    token_plain = secrets.token_urlsafe(32)
    db = get_db()
    db.create_token(body.token_name, token_plain, body.role, body.description or "")
    return token_plain

@router.get("/", response_model=List[TokenOut])
def list_tokens():
    db = get_db()
    tokens = db.list_tokens()
    return [
        TokenOut(
            token_name=t["token_name"],
            role=t["role"],
            description=t.get("description"),
            created_at=t.get("created_at"),
            revoked=bool(t.get("revoked", 0)),
        )
        for t in tokens
    ]

@router.post("/{token_name}/revoke")
def revoke_token(token_name: str, ):
    db = get_db()
    db.revoke_token(token_name)
    return {"ok": True}
