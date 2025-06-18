from typing import Optional, Dict, Any, List
import tempfile

import requests
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.models.db import SessionLocal, Conversation, Ticket

from app.logging_config import logger
from app.services.telephony import TelephonyService
from app.services.tts import TTSClient
from app.services.stt import STTClient
from app.services.intent import IntentClassifier
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


def _process_inbound_call(
    phone: str,
    provider_id: str,
    recording_url: str | None,
    transcript: str | None,
    locale: str,
) -> Dict[str, Any]:
    """Create/update Conversation and Ticket based on inbound payload."""
    session = SessionLocal()
    conv = session.query(Conversation).filter_by(external_id=provider_id).first()
    if not conv:
        conv = Conversation(
            phone=phone,
            direction="INBOUND",
            locale=locale,
            external_id=provider_id,
            start_ts=datetime.utcnow(),
            updated_ts=datetime.utcnow(),
        )
        session.add(conv)
        session.commit()
    else:
        conv.updated_ts = datetime.utcnow()

    if recording_url and not transcript:
        response = requests.get(recording_url)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(response.content)
            audio_path = tmp.name
        stt = STTClient(locale=locale)
        transcript = stt.transcribe(audio_path)

    if transcript:
        conv.transcript = transcript
        intent = IntentClassifier().classify(transcript)
    else:
        intent = "OTHER"
    conv.intents = [intent]
    conv.end_ts = datetime.utcnow()
    conv.status = "CLOSED" if intent != "LIVE_AGENT" else "OPEN"
    session.add(conv)
    session.commit()

    if intent != "LIVE_AGENT":
        ticket = session.query(Ticket).filter(Ticket.conversation_id == conv.id).first()
        if not ticket:
            ticket = Ticket(
                conversation_id=conv.id,
                category=intent,
                status="OPEN",
                created_ts=datetime.utcnow(),
                updated_ts=datetime.utcnow(),
            )
            session.add(ticket)
        else:
            ticket.category = intent
            ticket.status = "OPEN"
            ticket.updated_ts = datetime.utcnow()
        session.commit()
        return {"ticket_id": ticket.id, "status": "ticket_created", "intent": intent}

    session.commit()
    return {"status": "handoff", "message": "Routed to live agent simulator"}


@router.post("/webhook/twilio")
async def inbound_twilio(request: Request):
    if request.headers.get("content-type", "").startswith("application/json"):
        data = await request.json()
    else:
        data = await request.form()

    phone = data.get("From") or data.get("from")
    call_sid = data.get("CallSid") or data.get("call_sid")
    recording_url = data.get("RecordingUrl") or data.get("recording_url")
    transcript = (
        data.get("TranscriptionText")
        or data.get("SpeechResult")
        or data.get("transcript")
    )
    locale = data.get("Language", "en-US")

    return _process_inbound_call(phone, call_sid, recording_url, transcript, locale)


@router.post("/webhook/vapi")
async def inbound_vapi(request: Request):
    data = await request.json()

    phone = data.get("from") or data.get("phone")
    call_id = data.get("call_id") or data.get("id")
    recording_url = data.get("recordingUrl") or data.get("recording_url")
    transcript = data.get("transcript")
    locale = data.get("language", "en-US")

    return _process_inbound_call(phone, call_id, recording_url, transcript, locale)


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
    conv = (
        session.query(Conversation).filter(Conversation.id == conversation_id).first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv
