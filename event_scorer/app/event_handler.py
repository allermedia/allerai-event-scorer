from flask import abort, jsonify
from event_scorer import EventScorer
from pubsub import PubSubService
from werkzeug.exceptions import BadRequest
import json
import base64

class EventHandler:
    def __init__(self, project_id: str, output_topic: str):
        self.event_scorer = EventScorer()
        self.pubsub_service = PubSubService(project_id, output_topic)

    def process_request(self, request):
        try:
            payload, attributes = self.parse_request(request)

            if payload is None:
                print("Skipping processing due to invalid JSON payload.")
                return jsonify({"status": "error", "reason": "Invalid JSON payload"}), 400

            #self.pubsub_service.publish(payload)

            return jsonify({"status": "queued"}), 202


        except Exception as e:
            print(f"Error processing message: {e}")
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
    
    def enrichment_push(self, payload):
        return