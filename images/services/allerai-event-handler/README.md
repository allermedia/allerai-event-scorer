## Event Handler

This Flask-based service processes incoming Pub/Sub messages containing JSON payloads, validates the payloads, and republishes each valid payload to another Pub/Sub topic. It logs processing status for each payload.

---

### 1. Overview

- **Pub/Sub** receives incoming events from authorized sources.
- **Event Handler Cloud Run service**:
  - Parses incoming events.
  - Performs sanity checks and data validation.
  - Ensures required fields are present.
- Valid events are forwarded to the **Aller Data Platform (ADP)**.

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
