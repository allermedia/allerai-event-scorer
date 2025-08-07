# Event Handler Flask Service

This Flask-based service processes incoming Pub/Sub messages containing JSON payloads, validates the payloads, and republishes each valid payload to another Pub/Sub topic. It logs processing status for each payload.

---

## Features

- Accepts Pub/Sub push messages with base64-encoded JSON payload.
- Supports single JSON objects or arrays of objects.
- Validates required fields and ISO 8601 date format in payload.
- Publishes each valid payload individually to a configured Pub/Sub topic.
- Logs each processing step and any errors.

## Configuration

This service requires two environment variables to be set:

- `TARGET_PROJECT_ID`: The Google Cloud Project ID where the output Pub/Sub topic resides.  
  This is usually different from the project where the service itself is deployed.
- `OUTPUT_TOPIC`: The name of the Pub/Sub topic to publish messages to.

---

## Setup

### Prerequisites

- Python 3.8+
- Google Cloud SDK installed and configured
- Pub/Sub topics created in your GCP project
- `pubsub.py` module with `PubSubService` client (must be implemented separately)

### Installation

1. Clone the repo

2. Install dependencies

```bash
pip install -r requirements.txt
```
