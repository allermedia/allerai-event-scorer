from flask import Response, abort, jsonify
from pubsub import PubSubService
import re
import json
import base64
from typing import Any, Dict, Optional, Union, List, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class EventHandler:
    def __init__(self, project_id: str, output_topic: str, output_topic_error_log: str):
        self.pubsub_service = PubSubService(project_id, output_topic)
        self.pubsub_service_error_log = PubSubService(project_id, output_topic_error_log)

    def process_request(self, request) -> Tuple[Optional[Any], Dict[str, Any]]:

        try:
            payloads, attributes, message_id = self.parse_request(request)

            if payloads is None:
                return jsonify({"status": "error", "reason": "Invalid JSON payload"}), 400
            
            if isinstance(payloads, dict):
                payloads = [payloads]
            elif not isinstance(payloads, list):
                return jsonify({"status": "error", "reason": "Payload must be JSON object or list"}), 400

            for i, payload in enumerate(payloads):                
                current_id = payload.get("id", f"index_{i}")
                logger.info(f"Processing payload with id: {current_id}")
                self.validate_payload(payload)
                self.pubsub_service.publish(payload)
                logger.info(f"Published payload with id: {current_id}")

            return jsonify({"status": "success", "processed_count": len(payloads)}), 202
    
        except ValueError as e:
            print(f"Bad request {message_id}: {e}")
            try:
                article_id = payload.get("article_id")
                if article_id is None:
                    raise KeyError("article_id not found in payload")
            except (AttributeError, KeyError):
                article_id = None

            error_log = {
                "message_id": message_id,
                "article_id": article_id,
                "error": str(e)
            }
            
            self.pubsub_service_error_log.publish(error_log, {})
            return jsonify({"error": str(e)}), 200
        
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        
    def parse_request(self, request) -> tuple:
        envelope = request.get_json()
        if not envelope or "message" not in envelope:
            raise ValueError("No Pub/Sub message received")

        message = envelope["message"]
        data = message.get("data")
        if not data:
            raise ValueError("No data in Pub/Sub message")

        try:
            payload = json.loads(base64.b64decode(data).decode("utf-8"))
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON decoding error: {e}")

        attributes = message.get("attributes", {})
        message_id = message.get("messageId") 

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
        