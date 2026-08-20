from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import DatabaseSession, DemoUser
from app.schemas.merchants import MerchantListResponse, MerchantSort, SortDirection
from app.services.merchants import MerchantListParams, list_merchants

router = APIRouter(prefix="/merchants", tags=["merchants"])


@router.get("", response_model=MerchantListResponse)
async def merchants(
    _demo_user: DemoUser,
    session: DatabaseSession,
    search: Annotated[str | None, Query(max_length=128)] = None,
    category_id: Annotated[str | None, Query(max_length=64)] = None,
    sort: MerchantSort = MerchantSort.session_count,
    direction: SortDirection = SortDirection.desc,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=10, le=100)] = 20,
) -> MerchantListResponse:
    return await list_merchants(
        session,
        MerchantListParams(
            search=search,
            category_id=category_id,
            sort=sort,
            direction=direction,
            page=page,
            page_size=page_size,
        ),
    )
