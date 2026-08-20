from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transactions import Merchant, MerchantCategory, PaymentSession
from app.schemas.auth import MerchantCategorySummary, SelectedMerchant

AUTHENTICATED_KEY = "authenticated"
MERCHANT_KEY = "merchant_key"


def establish_demo_session(request: Request) -> None:
    request.session.clear()
    request.session[AUTHENTICATED_KEY] = True


def clear_demo_session(request: Request) -> None:
    request.session.clear()


def select_merchant_for_session(request: Request, merchant_key: str) -> None:
    request.session[MERCHANT_KEY] = merchant_key


async def get_selected_merchant(
    session: AsyncSession, merchant_key: str
) -> SelectedMerchant | None:
    merchant = await session.scalar(select(Merchant).where(Merchant.merchant_key == merchant_key))
    if merchant is None:
        return None

    category_rows = (
        await session.execute(
            select(MerchantCategory.category_id, MerchantCategory.title_fa)
            .join(PaymentSession, PaymentSession.category_id == MerchantCategory.category_id)
            .where(PaymentSession.merchant_id == merchant.id)
            .distinct()
            .order_by(MerchantCategory.category_id)
        )
    ).all()
    return SelectedMerchant(
        merchant_key=merchant.merchant_key,
        categories=[
            MerchantCategorySummary(category_id=row.category_id, title_fa=row.title_fa)
            for row in category_rows
        ],
    )
