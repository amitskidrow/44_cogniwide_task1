from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.logging_config import logger
from sqlalchemy.orm import Session
from app.models.db import get_db

router = APIRouter()


class OutboundCallRequest(BaseModel):
    phone: str
    prompt: str


@router.post("/call/outbound")
async def call_outbound(
    payload: OutboundCallRequest,
    db: Session = Depends(get_db),
):
    logger.bind(intent="OUTBOUND_CALL", phone=payload.phone).info("start")
    # Placeholder for outbound call initiation logic
    logger.bind(intent="OUTBOUND_CALL", phone=payload.phone).info("end")
    return {"status": "initiated"}


class IntentPayload(BaseModel):
    intent: str
    transcript: str


@router.post("/webhook/twilio")
async def inbound_twilio(
    payload: IntentPayload,
    db: Session = Depends(get_db),
):
    logger.bind(intent=payload.intent).info("start")
    # Placeholder for inbound call handling logic
    logger.bind(intent=payload.intent).info("end")
    return {"status": "received"}
