import json
from google.cloud import pubsub_v1

class PubSubService:
    def __init__(self, project_id: str, output_topic: str):
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(project_id, output_topic)

    def publish(self, message_dict: dict, attributes: dict):
        message_bytes = json.dumps(message_dict).encode('utf-8')
        self.publisher.publish(self.topic_path, message_bytes, **(attributes or {}))
