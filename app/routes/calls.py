from fastapi import APIRouter
from pydantic import BaseModel
from app.logging_config import logger

router = APIRouter()


class OutboundCallRequest(BaseModel):
    phone: str
    prompt: str


@router.post("/call/outbound")
async def call_outbound(payload: OutboundCallRequest):
    ctx = {
        "phone_number": payload.phone,
        "intent": "OUTBOUND_CALL",
        "conversation_id": None,
    }
    logger.bind(**ctx).info("call_outbound.start")
    # Placeholder for outbound call initiation logic
    logger.bind(**ctx).info("call_outbound.end")
    return {"status": "initiated"}


class IntentPayload(BaseModel):
    intent: str
    transcript: str


@router.post("/webhook/twilio")
async def inbound_twilio(payload: IntentPayload):
    ctx = {
        "phone_number": None,
        "intent": payload.intent,
        "conversation_id": None,
    }
    logger.bind(**ctx).info("inbound_twilio.start")
    # Placeholder for inbound call handling logic
    logger.bind(**ctx).info("inbound_twilio.end")
    return {"status": "received"}
