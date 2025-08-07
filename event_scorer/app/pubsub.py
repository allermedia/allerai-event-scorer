import json
from google.cloud import pubsub_v1

class PubSubService:
    def __init__(self):
        self.publisher = pubsub_v1.PublisherClient()
        self._topic_path_cache = {}

    def _get_topic_path(self, project_id: str, topic_id: str) -> str:
        key = f"{project_id}/{topic_id}"
        if key not in self._topic_path_cache:
            self._topic_path_cache[key] = self.publisher.topic_path(project_id, topic_id)
        return self._topic_path_cache[key]

    def publish(self, project_id: str, topic_id: str, message_dict: dict, attributes: dict = None):
        topic_path = self._get_topic_path(project_id, topic_id)
        message_bytes = json.dumps(message_dict).encode('utf-8')
        self.publisher.publish(topic_path, message_bytes, **(attributes or {}))
