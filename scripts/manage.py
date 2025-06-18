import argparse
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models.db import SessionLocal, Conversation, Ticket


def delete_conversation(conv_id: int) -> None:
    session = SessionLocal()
    conv = session.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv:
        print(f"Conversation {conv_id} not found")
        return
    session.delete(conv)
    session.commit()
    print(f"Deleted conversation {conv_id}")


def delete_ticket(ticket_id: int) -> None:
    session = SessionLocal()
    ticket = session.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        print(f"Ticket {ticket_id} not found")
        return
    session.delete(ticket)
    session.commit()
    print(f"Deleted ticket {ticket_id}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage Voice Agent records")
    sub = parser.add_subparsers(dest="command", required=True)

    dc = sub.add_parser("delete-conversation", help="Delete a conversation by ID")
    dc.add_argument("id", type=int, help="Conversation ID")

    dt = sub.add_parser("delete-ticket", help="Delete a ticket by ID")
    dt.add_argument("id", type=int, help="Ticket ID")

    args = parser.parse_args()
    if args.command == "delete-conversation":
        delete_conversation(args.id)
    elif args.command == "delete-ticket":
        delete_ticket(args.id)


if __name__ == "__main__":
    main()
