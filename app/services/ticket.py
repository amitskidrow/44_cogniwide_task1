from datetime import datetime
from app.models.db import SessionLocal, Ticket


class TicketService:
    """Service for creating support tickets."""

    def __init__(self, session: SessionLocal | None = None) -> None:
        self.session = session or SessionLocal()

    def create_ticket(self, conversation_id: int, category: str) -> Ticket:
        ticket = Ticket(
            conversation_id=conversation_id,
            category=category,
            status="OPEN",
            created_ts=datetime.utcnow(),
        )
        self.session.add(ticket)
        self.session.commit()
        self.session.refresh(ticket)
        return ticket

