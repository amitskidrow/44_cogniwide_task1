import os
from sqlalchemy import (
    create_engine, Column, Integer, String, Enum, DateTime, ForeignKey, Text, JSON
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

class Conversation(Base):
    """Database model for a phone conversation."""

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True)
    phone = Column(String(20))
    direction = Column(Enum("INBOUND", "OUTBOUND", name="direction_enum"))
    start_ts = Column(DateTime)
    end_ts = Column(DateTime)
    transcript = Column(Text)
    intents = Column(JSON)
    status = Column(Enum("OPEN", "CLOSED", name="conversation_status"), default="OPEN")

    tickets = relationship("Ticket", back_populates="conversation")


class Ticket(Base):
    """Support ticket generated from a conversation."""

    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    category = Column(String(100))
    status = Column(Enum(
        "OPEN",
        "RESOLVED",
        "ESCALATED",
        name="ticket_status"
    ), default="OPEN")
    created_ts = Column(DateTime)
    resolved_ts = Column(DateTime)

    conversation = relationship("Conversation", back_populates="tickets")


def _build_database_url() -> str:
    """Assemble a connection URL from individual DB_* variables if provided."""
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return db_url

    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    name = os.getenv("DB_NAME")

    if all([host, port, user, password, name]):
        return f"postgresql://{user}:{password}@{host}:{port}/{name}"

    return "sqlite:///./app.db"


def get_engine() -> "Engine":
    """Create a SQLAlchemy engine, defaulting to a local SQLite DB."""
    db_url = _build_database_url()
    connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
    return create_engine(db_url, connect_args=connect_args)

engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_sessionmaker() -> sessionmaker:
    """Return a configured sessionmaker bound to the engine."""
    return SessionLocal


def get_db():
    """Yield a SQLAlchemy session for request handlers."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create database tables if they do not exist."""
    Base.metadata.create_all(bind=engine)

