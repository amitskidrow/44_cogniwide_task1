from typing import Optional, Dict, Any, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.telephony import TelephonyService
from app.services.stt import STTClient
from app.services.intent import IntentClassifier
from app.models.db import SessionLocal, Conversation, Ticket
from datetime import datetime

router = APIRouter()


class OutboundCallRequest(BaseModel):
    phone: str
    prompt: str
    metadata: Optional[Dict[str, Any]] = None
    locale: Optional[str] = "en-US"


@router.post("/call/outbound")
async def call_outbound(payload: OutboundCallRequest):
    telephony = TelephonyService()
    await telephony.start_outbound_call(payload.phone, payload.prompt, payload.metadata)
    session = SessionLocal()
    conv = Conversation(
        phone=payload.phone,
        direction="OUTBOUND",
        locale=payload.locale,
        start_ts=datetime.utcnow(),
        transcript="",
        status="OPEN",
    )
    session.add(conv)
    session.commit()
    return {"conversation_id": conv.id, "status": "started"}


class InboundCallRequest(BaseModel):
    phone: str
    locale: Optional[str] = "en-US"


class StreamEvent(BaseModel):
    event: Dict[str, Any]


@router.post("/webhook/twilio")
async def inbound_twilio(payload: InboundCallRequest):
    session = SessionLocal()
    conv = Conversation(
        phone=payload.phone,
        direction="INBOUND",
        locale=payload.locale,
        start_ts=datetime.utcnow(),
        transcript="",
        status="OPEN",
    )
    session.add(conv)
    session.commit()
    return {"conversation_id": conv.id, "status": "started"}

@router.post("/webhook/vapi")
async def inbound_vapi(payload: InboundCallRequest):
    return await inbound_twilio(payload)


@router.post("/webhook/stream/{conversation_id}")
async def stream_conversation(conversation_id: int, payload: StreamEvent):
    session = SessionLocal()
    conv = session.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    stt = STTClient(locale=conv.locale)
    text = stt.extract_event_transcript(payload.event)
    if text:
        conv.transcript = (conv.transcript or "") + text + " "
        session.add(conv)
        session.commit()

    if payload.event.get("event") == "call_end":
        conv.end_ts = datetime.utcnow()
        conv.status = "CLOSED"
        intent = IntentClassifier().classify(conv.transcript)
        conv.intents = [intent]
        session.add(conv)
        session.commit()
        if intent != "LIVE_AGENT":
            ticket = Ticket(
                conversation_id=conv.id,
                category=intent,
                status="OPEN",
                created_ts=datetime.utcnow(),
            )
            session.add(ticket)
            session.commit()

    return {"status": "ok"}

class TicketResponse(BaseModel):
    id: int
    conversation_id: int
    category: str
    status: str
    created_ts: datetime
    resolved_ts: Optional[datetime] = None

    class Config:
        orm_mode = True

class ConversationResponse(BaseModel):
    id: int
    phone: str
    direction: str
    locale: Optional[str]
    start_ts: datetime
    end_ts: Optional[datetime] = None
    transcript: str
    intents: List[str]
    status: str
    tickets: List[TicketResponse] = []

    class Config:
        orm_mode = True

@router.get("/conversation/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: int):
    session = SessionLocal()
    conv = session.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv
