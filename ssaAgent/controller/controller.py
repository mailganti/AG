#!/usr/bin/env python3
from fastapi import FastAPI
from controller.api.agents import router as agents_router
from controller.api.workflows import router as workflows_router
from controller.api.scripts import router as scripts_router
from controller.api.tokens import router as tokens_router
import os


ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")

from fastapi import Header,HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(title="Orchestration Controller Testing", redirect_slashes=True)

BASE_DIR = os.path.join(os.path.dirname(__file__))
UI_DIR = os.path.join(BASE_DIR,"ui")

app.mount("/",StaticFiles(directory=UI_DIR,html=True),name="ui")

print (">>> Serving UI from:" , UI_DIR)

app.include_router(agents_router)
app.include_router(workflows_router)
app.include_router(scripts_router)
app.include_router(tokens_router)



@app.get("/ui/register_agent")

def serve_register_agent():
    ui_path = os.path.join(os.path.dirname(__file__),"..","ui","register_agent.html")
    return FileResponse(ui_path)


from fastapi.middleware.cors import CORSMiddleware

#ui_path = os.path.join(os.path.dirname(__file__),"..","ui")
#app.mount("/ui",StaticFiles(directory=ui_path),name="ui")
#app.mount("/ui",StaticFiles(directory=ui_path,html=True),name="ui")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(agents_router, prefix="/api/agents", tags=["agents"])
app.include_router(workflows_router, prefix="/api/workflows", tags=["workflows"])
app.include_router(scripts_router, prefix="/api/scripts", tags=["scripts"])
app.include_router(tokens_router, prefix="/api/tokens", tags=["tokens"])

@app.get("/healthz")
def healthz():
    return {"status": "ok"}
