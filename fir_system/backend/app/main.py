"""
app/main.py
FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from fir_system.app.database  import init_db
from fir_system.app.ml_models import load_all
from fir_system.app.routes    import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("── Initialising database ──")
    init_db()
    print("── Loading ML models ──")
    load_all()
    yield


app = FastAPI(
    title       = "FIR Generator System",
    description = "Audio complaint → NLP extraction → MySQL storage",
    version     = "1.0.0",
    lifespan    = lifespan,
)

# Allow the frontend (same origin or dev server) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins  = ["*"],
    allow_methods  = ["*"],
    allow_headers  = ["*"],
)

# API routes
app.include_router(router)

# Serve the frontend static files
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
FRONTEND_DIR = os.path.abspath(FRONTEND_DIR)

if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_frontend(full_path: str):
        target = os.path.join(FRONTEND_DIR, full_path)
        if os.path.isfile(target):
            return FileResponse(target)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
