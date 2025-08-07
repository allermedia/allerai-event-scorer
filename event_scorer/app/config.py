import google.auth

credentials, project_id = google.auth.default()

PROJECT_ID = project_id
OUTPUT_TOPIC = "allerai-scorer-events-push"
ENRICHMENT_PROJECT_ID = "aller-data-platform-prod-1f89"
ENRICHMENT_TOPIC= "pages_events"
