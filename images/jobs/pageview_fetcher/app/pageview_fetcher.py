from google.cloud import bigquery
import dlt
import google.auth
from google.api_core.exceptions import NotFound

@dlt.resource(name="pages_pageviews", primary_key="page_id")
def get_pageviews(from_date, to_date):
    print(f"Fetching data from {from_date} to {to_date}")
    source_project_id = "aller-data-platform-prod-1f89"
    source_dataset = "editorial"
    source_table = "web_traffic_pageviews"

    client = bigquery.Client()
    # Get existing page_id from target table to avoid duplicates
    existing_dates = get_existing_dates(client, from_date, to_date)

    credentials, project_id = google.auth.default()
    print(f"Project ID: {project_id}")

    source_query = f"""
        SELECT
            event_date,
            page_id,
            market,
            site_domain,
            COUNT(*) AS pageview_count
        FROM 
            `{source_project_id}.{source_dataset}.{source_table}`
        WHERE 
            event_date BETWEEN '{from_date}' AND '{to_date}'
        AND
            page_id IS NOT NULL
        GROUP BY 
            event_date, page_id, market, site_domain
    """
    source_job = client.query(source_query)

    for row in source_job:
        if row.event_date in existing_dates:
            print(f"Skipping already-loaded date: {row.event_date}")
        if row.event_date not in existing_dates:
            yield dict(row)

def get_existing_dates(target_client, from_date, to_date):
    target_dataset = "adp_pageviews"
    target_table = "page_pageviews"

    existing_dates_query = f"""
        SELECT 
            DISTINCT(event_date) 
        FROM 
            `{target_client.project}.{target_dataset}.{target_table}`
        WHERE 
            event_date BETWEEN '{from_date}' AND '{to_date}'
    """
    try:
        existing_dates_job = target_client.query(existing_dates_query)
        return {row.event_date for row in existing_dates_job}
    except NotFound:
        return set()
    