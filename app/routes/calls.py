from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from app.services.telephony import TelephonyService
from app.models.db import SessionLocal, Conversation
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
    result = await telephony.start_outbound_call(
        payload.phone, payload.prompt, payload.metadata
    )

    session = SessionLocal()
    conv = Conversation(
        phone=payload.phone,
        direction="OUTBOUND",
        locale=payload.locale,
        start_ts=datetime.utcnow(),
        status="OPEN",
    )
    session.add(conv)
    session.commit()

    return {"conversation_id": conv.id, "call_sid": result.get("sid")}


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
