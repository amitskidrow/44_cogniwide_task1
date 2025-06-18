from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Generator, List
from sqlalchemy.orm import Session

from app.models.db import Conversation, get_sessionmaker

from app.services.telephony import TelephonyService

router = APIRouter()


def get_telephony_service() -> TelephonyService:
    return TelephonyService()


def get_db_session() -> Generator[Session, None, None]:
    SessionLocal = get_sessionmaker()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class OutboundCallRequest(BaseModel):
    phone_number: str
    prompt: str
    metadata: Dict[str, Any] | None = None


class WebhookEvent(BaseModel):
    """Generic inbound webhook payload."""

    event: Dict[str, Any]


@router.post("/call/outbound")
async def call_outbound(
    data: OutboundCallRequest,
    service: TelephonyService = Depends(get_telephony_service),
):
    """Trigger an outbound call via the telephony provider."""
    result = await service.start_outbound_call(
        phone_number=data.phone_number,
        prompt=data.prompt,
        metadata=data.metadata,
    )
    return result


@router.post("/call/inbound")
async def call_inbound(
    event: WebhookEvent, service: TelephonyService = Depends(get_telephony_service)
):
    """Handle inbound call events from Twilio/Vapi."""
    result = await service.handle_inbound_call(event.event)
    return result


@router.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: int, db: Session = Depends(get_db_session)):
    """Return metadata for a conversation and any linked tickets."""
    conversation = (
        db.query(Conversation).filter(Conversation.id == conversation_id).first()
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    tickets: List[dict] = [
        {
            "id": t.id,
            "category": t.category,
            "status": t.status,
            "created_ts": t.created_ts,
            "resolved_ts": t.resolved_ts,
        }
        for t in conversation.tickets
    ]

    meta = {
        "id": conversation.id,
        "phone": conversation.phone,
        "direction": conversation.direction,
        "start_ts": conversation.start_ts,
        "end_ts": conversation.end_ts,
        "transcript": conversation.transcript,
        "intents": conversation.intents,
        "status": conversation.status,
    }

    return {"conversation": meta, "tickets": tickets}
