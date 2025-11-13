import dlt
import os
from pymongo import MongoClient
from google.cloud import bigquery
import google.auth
from google.api_core.exceptions import NotFound
from datetime import datetime, timezone, timedelta

@dlt.resource(name="citation_story_export", primary_key="_id")
def get_drafts():
    mongo_uri = os.getenv("MONGO_URI", "missing environment variable MONGO_URI")
    mongo_db = os.getenv("MONGO_DB", "missing environment variable MONGO_DB")
    mongo_collection = os.getenv("MONGO_COLLECTION", "missing environment variable MONGO_COLLECTION")
    bq_dataset = "platform_drafts"
    bq_table = "citation_story_export"

    # Get drafts from MongoDB
    mongo_client = MongoClient(mongo_uri)
    collection = mongo_client[mongo_db][mongo_collection]
    all_docs = list(collection.find())

    print(f"Fetched {len(all_docs)} documents from MongoDB.")

    # Get existing stored drafts from BigQuery
    existing_ids = get_bq_drafts(bq_dataset, bq_table)

    # Filter for drafts based on createdAt date (used for insert/update logic)
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    inserted, updated, skipped = 0, 0, 0

    for doc in all_docs:
        doc["_id"] = str(doc["_id"])

        createdAt = doc.get("createdAt")

        if isinstance(createdAt, str):
            try:
                createdAt = datetime.fromisoformat(createdAt.replace("Z", "+00:00"))
            except ValueError:
                createdAt = None
        elif not isinstance(createdAt, datetime):
            createdAt = None

        if createdAt is None:
            # If createdAt is missing or invalid, treat as new    
            if doc["_id"] not in existing_ids:
                inserted += 1
                yield doc
        else:
            if createdAt >= seven_days_ago:
                # Newer than 7 days → yield as update
                updated += 1
                yield doc
            else:
                # Older than 7 days → yield as insert if not already existing
                if doc["_id"] not in existing_ids:
                    inserted += 1
                    yield doc
                else:
                    skipped += 1

    print(f"Inserted: {inserted}, Updated: {updated}, Skipped: {skipped}")

def get_bq_drafts(dataset, table):
    credentials, project_id = google.auth.default()
    print(f"Project ID: {project_id}")
    
    bq_client = bigquery.Client(project=project_id)

    try:
        query = f"SELECT _id FROM `{project_id}.{dataset}.{table}`"
        existing_ids = {str(row["_id"]) for row in bq_client.query(query)}
        print(f"Found {len(existing_ids)} existing documents in BigQuery.")
    except NotFound:
        existing_ids = set()
        print("BigQuery table not found. Assuming initial load.")

    return existing_ids
