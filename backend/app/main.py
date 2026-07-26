"""
main.py

FastAPI entrypoint. Keeps app wiring separate from route logic
(app/api/routes.py) so other teammates' routers (if any get added
later — e.g. a settings/profile router) can be included here without
touching the dashboard routes.

Run with:
    uvicorn app.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as dashboard_router

app = FastAPI(title="ArmPilot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten before shipping past the hackathon
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard_router)
