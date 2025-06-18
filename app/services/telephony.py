import os
import tempfile
from datetime import datetime
from typing import Dict, Any, List

import requests
from twilio.rest import Client as TwilioClient

from app.models.db import get_sessionmaker, Conversation
from app.services.tts import TTSClient
from app.services.stt import STTClient
from app.services.intent import IntentClassifier

class TelephonyService:
    """Telephony interactions using Twilio/Vapi clients and NLP helpers."""

    def __init__(self) -> None:
        self.twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_FROM_NUMBER")
        self.client = None
        if self.twilio_sid and self.twilio_token:
            self.client = TwilioClient(self.twilio_sid, self.twilio_token)

        self.tts = TTSClient()
        self.stt = STTClient()
        self.intent = IntentClassifier()
        self.Session = get_sessionmaker()

    async def start_outbound_call(
        self, phone_number: str, prompt: str, metadata: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        """Initiate an outbound call and create a Conversation row."""

        session = self.Session()
        conversation = Conversation(
            phone=phone_number,
            direction="OUTBOUND",
            start_ts=datetime.utcnow(),
            intents=[],
        )
        session.add(conversation)
        session.commit()
        session.refresh(conversation)

        twiml = self.tts.synthesize(prompt)
        call_sid = "simulated"
        if self.client and self.from_number:
            call = self.client.calls.create(
                twiml=twiml.decode() if isinstance(twiml, bytes) else twiml,
                to=phone_number,
                from_=self.from_number,
                status_callback=metadata.get("callback_url") if metadata else None,
                status_callback_event=["completed"] if metadata else None,
            )
            call_sid = call.sid

        return {"conversation_id": conversation.id, "call_sid": call_sid}

    async def handle_inbound_call(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process inbound webhook events and persist transcript & intent."""

        conversation_id = int(event.get("conversation_id", 0))
        session = self.Session()
        conversation = session.get(Conversation, conversation_id)
        if not conversation:
            return {"status": "error", "detail": "conversation_not_found"}

        transcript = ""
        if "transcript" in event:
            transcript = event["transcript"]
        elif "recording_url" in event:
            resp = requests.get(event["recording_url"], timeout=10)
            resp.raise_for_status()
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(resp.content)
                audio_path = tmp.name
            transcript = self.stt.transcribe(audio_path)
            os.remove(audio_path)

        intent = self.intent.classify(transcript) if transcript else "OTHER"

        conversation.transcript = (conversation.transcript or "") + transcript + "\n"
        intents: List[str] = conversation.intents or []
        intents.append(intent)
        conversation.intents = intents

        if event.get("completed"):
            conversation.end_ts = datetime.utcnow()
            conversation.status = "CLOSED"

        session.add(conversation)
        session.commit()
        return {"status": "processed", "intent": intent, "conversation_id": conversation.id}

