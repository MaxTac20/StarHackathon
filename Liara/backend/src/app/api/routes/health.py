from fastapi import APIRouter

from app.api.deps import DatabaseSession
from app.schemas.health import HealthResponse, ReadyResponse
from app.services.health import check_database

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse()


@router.get("/ready", response_model=ReadyResponse)
async def ready(session: DatabaseSession) -> ReadyResponse:
    await check_database(session)
    return ReadyResponse()
