from flask import Request
import functions_framework
from event_handler import EventHandler
from config import PROJECT_ID, OUTPUT_TOPIC, OUTPUT_TOPIC_ERROR_LOG, ADP_PROJECT_ID

handler = EventHandler(PROJECT_ID, OUTPUT_TOPIC, OUTPUT_TOPIC_ERROR_LOG, ADP_PROJECT_ID)

@functions_framework.http
def process_request(request: Request):
    return handler.process_request(request)
