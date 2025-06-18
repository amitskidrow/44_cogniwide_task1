from fastapi import APIRouter
from pydantic import BaseModel

from app.config import get_default_locale, set_default_locale

router = APIRouter()


class LocaleUpdateRequest(BaseModel):
    locale: str


@router.get("/config/locale")
async def read_locale():
    return {"default_locale": get_default_locale()}


@router.post("/config/locale")
async def update_locale(payload: LocaleUpdateRequest):
    set_default_locale(payload.locale)
    return {"default_locale": payload.locale}
