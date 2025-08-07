from flask import Response, abort, jsonify
from pubsub import PubSubService
from werkzeug.exceptions import BadRequest
import json
import base64
from typing import Any, Dict, Optional, Union, List, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class EventHandler:
    def __init__(self, project_id: str, output_topic: str):
        self.pubsub_service = PubSubService(project_id, output_topic)

    def process_request(self, request) -> Tuple[Optional[Any], Dict[str, Any]]:

        try:
            payloads, attributes = self.parse_request(request)

            if payloads is None:
                return jsonify({"status": "error", "reason": "Invalid JSON payload"}), 400
            
            if isinstance(payloads, dict):
                payloads = [payloads]
            elif not isinstance(payloads, list):
                return jsonify({"status": "error", "reason": "Payload must be JSON object or list"}), 400

            for i, payload in enumerate(payloads):                
                current_id = payload.get("id", f"index_{i}")
                logger.info(f"Processing payload with id: {current_id}")
                try:
                    self.validate_payload(payload)
                    self.pubsub_service.publish(payload)
                    logger.info(f"Published payload with id: {current_id}")
                except Exception as e:
                    logger.exception(f"Failed to process payload with id {current_id}: {e}")

            return jsonify({"status": "success", "processed_count": len(payloads)}), 202
        
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        
    def parse_request(self,request) -> dict:
        envelope = request.get_json()

        if not envelope or "message" not in envelope:
            abort(400, "No Pub/Sub message received")

        message = envelope["message"]
        data = message.get("data")
        if not data:
            abort(400, "No data in Pub/Sub message")

        try:
            payload = json.loads(base64.b64decode(data).decode("utf-8"))
        except json.JSONDecodeError as e:
            print(f"JSON decoding error: {e}")
            return None, None
        
        attributes = message.get("attributes", {})

        return payload, attributes
    
        
    def validate_payload(self, payload: Dict[str, Any]) -> None:
        required_fields = ["id", "published", "site", "teaser", "title", "body"]

        for field in required_fields:
            if field not in payload:
                raise ValueError(f"Missing required field: {field}")
            if not isinstance(payload[field], str) and field != "published":
                raise ValueError(f"Field '{field}' must be a string")

        # Validate 'published' format
        published = payload["published"]

        if not isinstance(published, dict) or "$date" not in published:
            raise ValueError("Field 'published' must be a dict with a '$date' key")

        date_str = published["$date"]
        if not isinstance(date_str, str):
            raise ValueError("Field 'published[\"$date\"]' must be a string")

        try:
            # Validate ISO 8601 format with optional milliseconds and timezone
            datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError(f"Invalid ISO 8601 datetime format: {date_str}")