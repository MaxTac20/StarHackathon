from fastapi import APIRouter, HTTPException, Request, Response, status

from app.api.deps import DatabaseSession, DemoUser
from app.core.config import get_settings
from app.core.security import password_matches
from app.schemas.auth import LoginRequest, MerchantSelectionRequest, SessionResponse
from app.services.auth import (
    AUTHENTICATED_KEY,
    MERCHANT_KEY,
    clear_demo_session,
    establish_demo_session,
    get_selected_merchant,
    select_merchant_for_session,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=SessionResponse)
async def login(payload: LoginRequest, request: Request) -> SessionResponse:
    if not password_matches(payload.password, get_settings().app_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
    establish_demo_session(request)
    return SessionResponse(authenticated=True)


@router.get("/session", response_model=SessionResponse)
async def session_state(request: Request, session: DatabaseSession) -> SessionResponse:
    if request.session.get(AUTHENTICATED_KEY) is not True:
        return SessionResponse(authenticated=False)
    merchant_key = request.session.get(MERCHANT_KEY)
    if not isinstance(merchant_key, str):
        return SessionResponse(authenticated=True)
    merchant = await get_selected_merchant(session, merchant_key)
    if merchant is None:
        request.session.pop(MERCHANT_KEY, None)
    return SessionResponse(authenticated=True, selected_merchant=merchant)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request) -> Response:
    clear_demo_session(request)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/merchant", response_model=SessionResponse)
async def choose_merchant(
    payload: MerchantSelectionRequest,
    request: Request,
    _demo_user: DemoUser,
    session: DatabaseSession,
) -> SessionResponse:
    merchant = await get_selected_merchant(session, payload.merchant_key)
    if merchant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant not found")
    select_merchant_for_session(request, merchant.merchant_key)
    return SessionResponse(authenticated=True, selected_merchant=merchant)
