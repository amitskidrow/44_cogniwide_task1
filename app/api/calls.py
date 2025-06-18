from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any

from app.logging_config import logger

from app.services.telephony import TelephonyService

router = APIRouter()

def get_telephony_service() -> TelephonyService:
    return TelephonyService()

class OutboundCallRequest(BaseModel):
    phone_number: str
    prompt: str
    metadata: Dict[str, Any] | None = None

class WebhookEvent(BaseModel):
    """Generic inbound webhook payload."""
    event: Dict[str, Any]

@router.post("/call/outbound")
async def call_outbound(data: OutboundCallRequest, service: TelephonyService = Depends(get_telephony_service)):
    """Trigger an outbound call via the telephony provider."""
    ctx = {
        "phone_number": data.phone_number,
        "intent": data.metadata.get("intent") if data.metadata else None,
        "conversation_id": data.metadata.get("conversation_id") if data.metadata else None,
    }
    logger.bind(**ctx).info("outbound_call.start")
    result = await service.start_outbound_call(
        phone_number=data.phone_number,
        prompt=data.prompt,
        metadata=data.metadata,
    )
    logger.bind(**ctx).info("outbound_call.end")
    return result

@router.post("/call/inbound")
async def call_inbound(event: WebhookEvent, service: TelephonyService = Depends(get_telephony_service)):
    """Handle inbound call events from Twilio/Vapi."""
    payload = event.event
    ctx = {
        "phone_number": payload.get("from"),
        "intent": payload.get("intent"),
        "conversation_id": payload.get("conversation_id"),
    }
    logger.bind(**ctx).info("inbound_call.start")
    result = await service.handle_inbound_call(payload)
    logger.bind(**ctx).info("inbound_call.end")
    return result
