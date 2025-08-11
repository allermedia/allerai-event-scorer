from flask import jsonify
from pubsub import PubSubService
from parsers import RequestParser
from typing import Any, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class EventHandler:
    def __init__(self, project_id: str, output_topic: str, output_topic_error_log: str):
        self.request_parser = RequestParser()
        self.pubsub_service = PubSubService(project_id, output_topic)
        self.pubsub_service_error_log = PubSubService(project_id, output_topic_error_log)

    def process_request(self, request) -> Tuple[Optional[Any], Dict[str, Any]]:
        payload = None
        message_id = None

        try:
            payloads, attributes, message_id = self.request_parser.parse_request(request)

            if isinstance(payloads, dict):
                payloads = [payloads]
            elif not isinstance(payloads, list):
                return jsonify({"status": "error", "reason": "Payload must be dict or list"}), 400

            for i, payload in enumerate(payloads):
                current_id = payload.get("id", f"index_{i}")
                logger.info(f"Processing payload with id: {current_id}")
                self.request_parser.validate_payload(payload)
                self.pubsub_service.publish(payload)
                logger.info(f"Published payload for enrichment with id: {current_id}")
            
            return jsonify({"status": "success", "processed_count": len(payloads)}), 202

        except Exception as e:
            error_log = self.error_formatter(payload, message_id, e)
            self.pubsub_service_error_log.publish(error_log)
            return jsonify({"error": str(e)}), 200

    
    def error_formatter(self, payload: Dict[str, Any], message_id: str, e: Exception) -> Dict[str, Any]:
        try:
            article_id = payload.get("article_id") if payload else None
        except (AttributeError, KeyError):
            article_id = None

        error_log = {
            "message_id": message_id or None,
            "article_id": article_id,
            "error": str(e)
        }
        return error_log