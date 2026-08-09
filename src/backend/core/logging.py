import logging
import sys
import json
from datetime import datetime, timezone
from typing import Any, Dict
from src.backend.core.config import settings

class JSONLogFormatter(logging.Formatter):
    """Structured JSON formatter for production log aggregators."""
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "lineNo": record.lineno,
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "request_id"):
            log_data["request_id"] = getattr(record, "request_id")
        return json.dumps(log_data)

def setup_logging():
    """Configures root and component loggers."""
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Avoid duplicate handlers if setup is called multiple times
    if root_logger.handlers:
        root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    if settings.ENVIRONMENT == "production":
        handler.setFormatter(JSONLogFormatter())
    else:
        fmt = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(fmt)

    root_logger.addHandler(handler)

    # Silence noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)

def get_logger(name: str = "dota.backend") -> logging.Logger:
    """Retrieves a named logger instance."""
    return logging.getLogger(name)
