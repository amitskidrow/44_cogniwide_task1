from typing import Optional, Dict, Any, List
import tempfile

import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.logging_config import logger
from app.services.telephony import TelephonyService
from app.services.tts import TTSClient
from app.services.stt import STTClient
from app.services.intent import IntentClassifier
from app.models.db import SessionLocal, Conversation, Ticket, ProcessedWebhook
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
        start_ts=datetime.utcnow()
    )
    session.add(conv)
    session.commit()

    tts = TTSClient(locale=payload.locale)
    audio_bytes = tts.synthesize(payload.prompt)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(audio_bytes)
        audio_path = tmp.name

    stt = STTClient(locale=payload.locale)
    transcript = stt.transcribe(audio_path)
    intent = IntentClassifier().classify(transcript)

    conv.transcript = transcript
    conv.intents = [intent]
    conv.end_ts = datetime.utcnow()
    conv.status = "CLOSED"
    session.add(conv)
    session.commit()

    return {"conversation_id": conv.id, "intent": intent}


class InboundCallRequest(BaseModel):
    request_id: str
    phone: str
    recording_url: str
    locale: Optional[str] = "en-US"


@router.post("/webhook/twilio")
async def inbound_twilio(payload: InboundCallRequest):
    session = SessionLocal()
    # Idempotency check for repeated webhooks
    existing = session.query(ProcessedWebhook).filter(
        ProcessedWebhook.request_id == payload.request_id
    ).first()
    if existing:
        return {"status": "duplicate"}

    session.add(ProcessedWebhook(request_id=payload.request_id))
    session.commit()
    conv = Conversation(
        phone=payload.phone,
        direction="INBOUND",
        locale=payload.locale,
        start_ts=datetime.utcnow()
    )
    session.add(conv)
    session.commit()

    response = requests.get(payload.recording_url)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(response.content)
        audio_path = tmp.name

    stt = STTClient(locale=payload.locale)
    transcript = stt.transcribe(audio_path)
    intent = IntentClassifier().classify(transcript)

    conv.transcript = transcript
    conv.intents = [intent]
    conv.end_ts = datetime.utcnow()
    conv.status = "OPEN"
    session.add(conv)
    session.commit()

    if intent != "LIVE_AGENT":
        ticket = Ticket(
            conversation_id=conv.id,
            category=intent,
            status="OPEN",
            created_ts=datetime.utcnow()
        )
        session.add(ticket)
        session.commit()
        return {"ticket_id": ticket.id, "status": "ticket_created", "intent": intent}

    return {"status": "handoff", "message": "Routed to live agent simulator"}

@router.post("/webhook/vapi")
async def inbound_vapi(payload: InboundCallRequest):
    return await inbound_twilio(payload)

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
    end_ts: datetime
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
