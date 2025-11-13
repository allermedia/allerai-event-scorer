import json
import base64
import pandas as pd
import numpy as np

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

        final_payload = payload.get("merged_payload", {})

        return final_payload, attributes, message_id

    def payload_to_df(self, payload: dict) -> pd.DataFrame:
        if not isinstance(payload, dict):
            raise ValueError("Payload must be a dictionary.")
        emb = payload.get("embeddings_en")
        if not isinstance(emb, list) or not emb or not all(isinstance(x, (float, int)) for x in emb):
            raise ValueError("Event embedding is missing or invalid.")
        payload["embeddings_en"] = np.array(emb, dtype=np.float32)
        return pd.DataFrame([payload])
