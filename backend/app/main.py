"""
ArmPilot FastAPI entrypoint.
Wires together: hardware detection -> workload classifier -> optimization engine -> runtime (Ollama) -> logging.
Owner: Member 2 (secondary: Member 3)
"""

from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(title="ArmPilot", version="0.1.0")
app.include_router(router)


@app.get("/")
def root() -> dict:
    return {"service": "ArmPilot API", "status": "ok"}
