from fastapi import APIRouter

from tutoring_manager_api.api.v1 import health

api_router = APIRouter()
api_router.include_router(health.router)
