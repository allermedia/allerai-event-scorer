from flask import Request
from event_handler import EventHandler
from config import PROJECT_ID, OUTPUT_TOPIC

handler = EventHandler(PROJECT_ID, OUTPUT_TOPIC)

def process_request(request: Request):
    return handler.process_request(request)
