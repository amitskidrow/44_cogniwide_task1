from typing import Optional, Dict, Any, List
import tempfile
import requests
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from app.services.telephony import TelephonyService
from app.services.tts import TTSClient
from app.services.stt import STTClient
from app.services.intent import IntentClassifier
from app.services.ticket import TicketService
from app.services.live_agent import LiveAgentSimulator
from app.config import get_default_locale
from app.models.db import SessionLocal, Conversation
from datetime import datetime

router = APIRouter()


class OutboundCallRequest(BaseModel):
    phone: str
    prompt: str
    metadata: Optional[Dict[str, Any]] = None
    locale: Optional[str] = None


@router.post("/call/outbound")
async def call_outbound(payload: OutboundCallRequest):
    locale = payload.locale or get_default_locale()
    telephony = TelephonyService()
    await telephony.start_outbound_call(payload.phone, payload.prompt, payload.metadata)
    session = SessionLocal()
    conv = Conversation(
        phone=payload.phone,
        direction="OUTBOUND",
        locale=locale,
        start_ts=datetime.utcnow()
    )
    session.add(conv)
    session.commit()

    tts = TTSClient(locale=locale)
    audio_bytes = tts.synthesize(payload.prompt)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(audio_bytes)
        audio_path = tmp.name

    stt = STTClient(locale=locale)
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
    phone: str
    recording_url: str
    locale: Optional[str] = None


@router.post("/call/inbound")
async def inbound_call(payload: InboundCallRequest):
    """Process a completed inbound call recording."""
    locale = payload.locale or get_default_locale()
    session = SessionLocal()
    conv = Conversation(
        phone=payload.phone,
        direction="INBOUND",
        locale=locale,
        start_ts=datetime.utcnow(),
    )
    session.add(conv)
    session.commit()

    audio_resp = requests.get(payload.recording_url)
    audio_resp.raise_for_status()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(audio_resp.content)
        audio_path = tmp.name

    stt = STTClient(locale=locale)
    transcript = stt.transcribe(audio_path)
    intent = IntentClassifier().classify(transcript)

    conv.transcript = transcript
    conv.intents = [intent]
    conv.end_ts = datetime.utcnow()
    conv.status = "CLOSED"
    session.add(conv)
    session.commit()

    ticket_id: int | None = None
    if intent != "LIVE_AGENT":
        ticket = TicketService(session).create_ticket(conv.id, intent)
        ticket_id = ticket.id
    else:
        LiveAgentSimulator().handoff(conv.id)

    return {"conversation_id": conv.id, "intent": intent, "ticket_id": ticket_id}

@router.post("/webhook/twilio")
async def inbound_twilio(request: Request) -> Response:
    form = await request.form()
    event = dict(form)
    telephony = TelephonyService()
    twiml = await telephony.handle_inbound_call(event)
    return Response(content=twiml, media_type="application/xml")

@router.post("/webhook/vapi")
async def inbound_vapi(request: Request) -> Response:
    return await inbound_twilio(request)

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
