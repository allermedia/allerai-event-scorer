from flask import jsonify
from pubsub import PubSubService
from parsers import RequestParser
from typing import Any, Dict, Optional, Tuple
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class EventHandler:
    def __init__(self, project_id: str, output_topic: str, output_topic_error_log: str):
        self.request_parser = RequestParser()
        self.pubsub_service = PubSubService(project_id, output_topic)
        self.pubsub_service_error_log = PubSubService(project_id, output_topic_error_log)

    def process_request(self, request) -> Tuple[Optional[Any], Dict[str, Any]]:
        payloads = None
        message_id = None

        try:
            payloads, attributes, message_id = self.request_parser.parse_request(request)

            if isinstance(payloads, dict):
                payloads = [payloads]
            elif not isinstance(payloads, list):
                 raise ValueError("Payload must be dict or list")

            for i, payload in enumerate(payloads):
                current_id = payload.get("id", f"index_{i}")
                logger.info(f"Processing payload with id: {current_id}")
                self.request_parser.validate_payload(payload)
                
                for html_field in ["title", "teaser", "body"]:
                    payload[html_field] = self._sanitize_html(payload[html_field])

                self.pubsub_service.publish(payload)
                logger.info(f"Published payload for enrichment with id: {current_id}")
            
            return jsonify({"status": "success", "processed_count": len(payloads)}), 200

        except Exception as e:
            error_log = self.error_formatter(payloads, message_id, e)
            self.pubsub_service_error_log.publish(error_log)
            return jsonify({"error": str(e)}), 202

    
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
    
    def _sanitize_html(self, html_content: str) -> str:
        soup = BeautifulSoup(html_content, "html.parser")
        lines = [line.strip() for line in soup.get_text(separator="\n").splitlines()]
        clean_text = "\n".join(line for line in lines if line)
        return clean_text
