from loguru import logger
import sys

# Configure structured logging
logger.remove()  # Remove default handler
logger.add(sys.stderr, format="{time:ISO8601} | {level} | {message}", serialize=True)

__all__ = ["logger"]
