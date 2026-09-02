"""Logging configuration using loguru."""
import sys

from loguru import logger


def setup_logger(level: str = "info") -> logger:
    """Configure and return the loguru logger.

    Args:
        level: Logging level (debug, info, warning, error, critical).

    Returns:
        Configured loguru logger instance.
    """
    # Remove default handler
    logger.remove()

    # Add console handler
    logger.add(
        sys.stdout,
        level=level.upper(),
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        enqueue=True,
    )

    return logger
