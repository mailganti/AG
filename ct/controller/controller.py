#!/usr/bin/env python3
import os
import sys
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Get the directory where this file is located
CONTROLLER_DIR = os.path.dirname(os.path.abspath(__file__))
print(f">>> Controller directory: {CONTROLLER_DIR}")

# Add the controller directory to Python path
if CONTROLLER_DIR not in sys.path:
    sys.path.insert(0, CONTROLLER_DIR)

ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")

app = FastAPI(title="Orchestration Controller Testing", redirect_slashes=True)

UI_DIR = os.path.join(CONTROLLER_DIR, "ui")
print(f">>> UI directory: {UI_DIR}")

# Mount UI
app.mount("/", StaticFiles(directory=UI_DIR, html=True), name="ui")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Debug endpoint
@app.get("/debug/routes")
async def debug_routes():
    routes = []
    for route in app.routes:
        route_info = {
            "path": getattr(route, "path", "N/A"),
            "name": getattr(route, "name", "N/A"),
            "methods": getattr(route, "methods", [])
        }
        routes.append(route_info)
    return JSONResponse(routes)

# Health check
@app.get("/health")
async def health_check():
    return {"status": "running"}

# Import routers using relative imports
try:
    print(">>> Importing API routers...")
    
    # Method 1: Try relative imports
    try:
        from .api.agents import router as agents_router
        print("✅ Agents router imported (relative)")
    except ImportError:
        # Method 2: Try absolute imports  
        from api.agents import router as agents_router
        print("✅ Agents router imported (absolute)")
    
    app.include_router(agents_router, prefix="")
    print("✅ Agents routes mounted at /api")
    
except Exception as e:
    print(f"❌ Failed to import agents router: {e}")
    # Create fallback
    from fastapi import APIRouter
    agents_router = APIRouter()
    
    @agents_router.get("/")
    async def get_agents_fallback():
        return [{"name": "fallback-agent", "status": "online"}]
    
    app.include_router(agents_router, prefix="")

# Repeat for other routers...
try:
    from .api.workflows import router as workflows_router
    app.include_router(workflows_router, prefix="")
    print("✅ Workflows routes mounted")
except Exception as e:
    print(f"❌ Workflows router: {e}")

try:
    from .api.scripts import router as scripts_router
    app.include_router(scripts_router, prefix="")
    print("✅ Scripts routes mounted")
except Exception as e:
    print(f"❌ Scripts router: {e}")

try:
    from .api.tokens import router as tokens_router
    app.include_router(tokens_router, prefix="")
    print("✅ Tokens routes mounted")
except Exception as e:
    print(f"❌ Tokens router: {e}")

# Print all routes on startup
@app.on_event("startup")
async def startup_event():
    print("\n" + "="*50)
    print("REGISTERED ROUTES:")
    for route in app.routes:
        if hasattr(route, 'path'):
            methods = getattr(route, 'methods', ['ANY'])
            print(f"  {list(methods)} {route.path}")
    print("="*50)

# Make sure we can run directly too
