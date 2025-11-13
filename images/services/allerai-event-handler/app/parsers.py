import json
import base64
import re
from typing import Any, Dict
from datetime import datetime

class RequestParser:
    def __init__(self):
        pass

    def parse_request(self, request) -> tuple:
        envelope = request.get_json()
        if not envelope or "message" not in envelope:
            raise ValueError("No Pub/Sub message received")

        message = envelope["message"]
        attributes = message.get("attributes", {})
        message_id = message.get("messageId") or None

        data = message.get("data")
        if not data:
            raise ValueError("No data in Pub/Sub message")

        try:
            payload = json.loads(base64.b64decode(data).decode("utf-8"))
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON decoding error: {e}")

        attributes = message.get("attributes", {})
        message_id = message.get("messageId") or None

        return payload, attributes, message_id
        
    def validate_payload(self, payload: Dict[str, Any]) -> None:
        required_fields = ["id", "published", "site", "teaser", "title", "body"]

        for field in required_fields:
            if field not in payload:
                raise ValueError(f"Missing required field: {field}")
            if not isinstance(payload[field], str):
                raise ValueError(f"Field '{field}' must be a string")

        published_str = payload["published"]

        match = re.search(r"\$date['\"]?\s*:\s*['\"]([^'\"]+)['\"]", published_str)
        if match:
            date_str = match.group(1)
        else:
            date_str = published_str

        try:
            datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError(f"Invalid ISO 8601 datetime format: {date_str}")