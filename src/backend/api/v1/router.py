from fastapi import APIRouter
from src.backend.api.v1 import health, players, auth, renders, keys, admin

api_v1_router = APIRouter()

# Include health check, players, auth, renders, keys & admin routers
api_v1_router.include_router(health.router)
api_v1_router.include_router(players.router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(renders.router)
api_v1_router.include_router(keys.router)
api_v1_router.include_router(admin.router)
