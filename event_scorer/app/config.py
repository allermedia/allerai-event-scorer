import google.auth

credentials, project_id = google.auth.default()

PROJECT_ID = project_id
OUTPUT_TOPIC = "allerai-scorer-events-push"
OUTPUT_TOPIC_ERROR_LOG = "allerai-scorer-events-push-error-log"
