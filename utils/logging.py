from config import config
import logging
import sys
import json
from typing import Literal, Any
from datetime import datetime, timezone

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log = {
            "time": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "type": getattr(record, "type", "SYSTEM"),
            "status": getattr(record, "status", None),
            "data": getattr(record, "data", None),
            "message": record.getMessage(),
        }
        return json.dumps(log, ensure_ascii=False)

logger = logging.getLogger("app")
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setFormatter(JsonFormatter())

file_handler = logging.FileHandler(config.main_log, encoding="utf-8")
file_handler.setFormatter(JsonFormatter())

logger.addHandler(console_handler)
logger.addHandler(file_handler)