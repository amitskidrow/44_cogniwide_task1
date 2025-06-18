from app.logging_config import logger


class LiveAgentSimulator:
    """Placeholder for handing off conversations to a live agent."""

    def handoff(self, conversation_id: int) -> None:
        logger.info(f"Handoff to live agent for conversation {conversation_id}")

