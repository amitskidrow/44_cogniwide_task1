from fastapi import APIRouter
from pydantic import BaseModel
from app.logging_config import logger

router = APIRouter()


class OutboundCallRequest(BaseModel):
    phone: str
    prompt: str


@router.post("/call/outbound")
async def call_outbound(payload: OutboundCallRequest):
    logger.bind(intent="OUTBOUND_CALL", phone=payload.phone).info("start")
    # Placeholder for outbound call initiation logic
    logger.bind(intent="OUTBOUND_CALL", phone=payload.phone).info("end")
    return {"status": "initiated"}


class IntentPayload(BaseModel):
    intent: str
    transcript: str


@router.post("/webhook/twilio")
async def inbound_twilio(payload: IntentPayload):
    logger.bind(intent=payload.intent).info("start")
    # Placeholder for inbound call handling logic
    logger.bind(intent=payload.intent).info("end")
    return {"status": "received"}
