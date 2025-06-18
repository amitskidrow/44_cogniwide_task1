from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any

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
    result = await service.start_outbound_call(
        phone_number=data.phone_number,
        prompt=data.prompt,
        metadata=data.metadata,
    )
    return result

@router.post("/call/inbound")
async def call_inbound(event: WebhookEvent, service: TelephonyService = Depends(get_telephony_service)):
    """Handle inbound call events from Twilio/Vapi."""
    result = await service.handle_inbound_call(event.event)
    return result
