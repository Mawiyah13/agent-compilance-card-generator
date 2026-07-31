from fastapi import APIRouter
from app.api.v1.endpoints import auth, cards, audit

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(cards.router, prefix="/cards", tags=["cards"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
