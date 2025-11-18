"""
Centralized logging configuration for all entry points.
"""

import logging
import colorlog
from collections import deque
from typing import Optional
from rich.console import Console
from rich.text import Text


class RichLogHandler(logging.Handler):
    """Custom log handler that stores logs for display in Rich TUI."""

    def __init__(self, max_logs: int = 50):
        super().__init__()
        self.log_buffer = deque(maxlen=max_logs)
        self.log_colors = {
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red bold",
        }

    def emit(self, record: logging.LogRecord) -> None:
        """Store log record in buffer."""
        try:
            msg = self.format(record)
            color = self.log_colors.get(record.levelname, "white")
            self.log_buffer.append((record.levelname, msg, color))
        except Exception:
            self.handleError(record)

    def get_logs(self) -> list[tuple[str, str, str]]:
        """Get all stored logs as (level, message, color) tuples."""
        return list(self.log_buffer)

    def clear(self) -> None:
        """Clear all stored logs."""
        self.log_buffer.clear()


def setup_logging(log_file: str = "app.log", log_level: int = logging.INFO) -> None:
    """
    Configure logging with colorlog console handler and file handler.

    Args:
        log_file: Path to log file
        log_level: Minimum log level for root logger
    """
    # Create formatters
    console_formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s %(white)s%(message)s",
        datefmt=None,
        reset=True,
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
        secondary_log_colors={},
        style="%",
    )

    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)-8s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Create console handler with colorlog
    console_handler = colorlog.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    # Create file handler
    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(file_formatter)

    # Configure root logger
    root_logger = colorlog.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Add handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)


def setup_tui_logging(
    log_file: str = "app.log",
    log_level: int = logging.INFO,
    tui_log_level: int = logging.INFO,
) -> RichLogHandler:
    """
    Configure logging for TUI with Rich handler and file handler.

    Args:
        log_file: Path to log file
        log_level: Minimum log level for root logger
        tui_log_level: Minimum log level for TUI display (usually INFO)

    Returns:
        RichLogHandler instance that can be used to retrieve logs for display
    """
    # Create formatters
    tui_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
    )

    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)-8s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Create Rich handler for TUI
    rich_handler = RichLogHandler(max_logs=50)
    rich_handler.setLevel(tui_log_level)
    rich_handler.setFormatter(tui_formatter)

    # Create file handler
    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(file_formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Add handlers
    root_logger.addHandler(rich_handler)
    root_logger.addHandler(file_handler)

    return rich_handler
