import os
from typing import Dict, Any

from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse

class TelephonyService:
    """Twilio/Vapi telephony integration used for outbound and inbound calls."""

    def __init__(self) -> None:
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.caller_id = os.getenv("TWILIO_CALLER_ID")
        self.stream_url = os.getenv("TWILIO_STREAM_URL")

        if not all([self.account_sid, self.auth_token, self.caller_id]):
            raise ValueError("Twilio credentials not configured")

        self._client = Client(self.account_sid, self.auth_token)

    async def start_outbound_call(
        self, phone_number: str, prompt: str, metadata: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        """Trigger an outbound call via Twilio."""

        vr = VoiceResponse()
        if self.stream_url:
            vr.connect().stream(url=self.stream_url)
        vr.say(prompt)

        call = self._client.calls.create(
            twiml=str(vr), to=phone_number, from_=self.caller_id
        )

        return {
            "status": "started",
            "provider": "twilio",
            "sid": call.sid,
            "phone_number": phone_number,
            "prompt": prompt,
            "metadata": metadata or {},
        }

    async def handle_inbound_call(self, event: Dict[str, Any]) -> str:
        """Return TwiML for an inbound Twilio call that streams audio."""

        vr = VoiceResponse()
        if self.stream_url:
            vr.connect().stream(url=self.stream_url)
        vr.say("Please begin speaking after the beep.")
        return str(vr)
