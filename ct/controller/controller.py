#!/usr/bin/env python3
import os
import sys
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Fix Python path - add the current directory
sys.path.append(os.path.dirname(__file__))

app = FastAPI(title="Orchestration Controller", redirect_slashes=True)

# Mount UI
UI_DIR = os.path.join(os.path.dirname(__file__), "ui")
app.mount("/", StaticFiles(directory=UI_DIR, html=True), name="ui")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers - use direct imports since we fixed the path
try:
    from api.agents import router as agents_router
    app.include_router(agents_router, prefix="/api")
    print("✅ Agents routes mounted")
except Exception as e:
    print(f"❌ Agents router failed: {e}")

try:
    from api.workflows import router as workflows_router
    app.include_router(workflows_router, prefix="/api")
    print("✅ Workflows routes mounted")
except Exception as e:
    print(f"❌ Workflows router failed: {e}")

try:
    from api.scripts import router as scripts_router
    app.include_router(scripts_router, prefix="/api")
    print("✅ Scripts routes mounted")
except Exception as e:
    print(f"❌ Scripts router failed: {e}")

try:
    from api.tokens import router as tokens_router
    app.include_router(tokens_router, prefix="/api")
    print("✅ Tokens routes mounted")
except Exception as e:
    print(f"❌ Tokens router failed: {e}")

# Health check
@app.get("/health")
async def health_check():
    return {"status": "running", "message": "Controller is working"}

# Debug routes
@app.on_event("startup")
async def startup_event():
    print("\n=== REGISTERED ROUTES ===")
    for route in app.routes:
        if hasattr(route, 'path'):
            methods = getattr(route, 'methods', ['ANY'])
            print(f"{list(methods)} {route.path}")
    print("=========================\n")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
