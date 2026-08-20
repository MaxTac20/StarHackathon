from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.transactions import Merchant
from app.services.auth import AUTHENTICATED_KEY, MERCHANT_KEY

DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


async def require_demo_user(request: Request) -> None:
    if request.session.get(AUTHENTICATED_KEY) is not True:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )


DemoUser = Annotated[None, Depends(require_demo_user)]


async def require_selected_merchant(
    request: Request, session: DatabaseSession, _demo_user: DemoUser
) -> Merchant:
    merchant_key = request.session.get(MERCHANT_KEY)
    if not isinstance(merchant_key, str):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Select a merchant first")
    merchant = await session.scalar(select(Merchant).where(Merchant.merchant_key == merchant_key))
    if merchant is None:
        request.session.pop(MERCHANT_KEY, None)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Selected merchant is unavailable"
        )
    return merchant


CurrentMerchant = Annotated[Merchant, Depends(require_selected_merchant)]
