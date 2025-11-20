from fastapi import Header,HTTPException 

import os

ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")

def require_admin(x_admin_token: str = Header(...,convert_underscores=False)):

    if x_admin_token is None:
        raise HTTPException(status_code=500, detail="ADMIN_TOKEN not configured")

    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="invalid_admin_token")
    
    return True
