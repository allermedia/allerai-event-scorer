import dlt
from pageview_fetcher import get_pageviews
import argparse
from datetime import datetime, timedelta

def run_pipeline(from_date=None, to_date=None):
    pipeline = dlt.pipeline(
        pipeline_name="adp_pageviews_to_bq_incremental",
        destination="bigquery",
        dataset_name="adp_pageviews"
    )

    print("Running pipeline...")

    try:
        load_info = pipeline.run(
            get_pageviews(from_date=from_date, to_date=to_date),
            write_disposition="append"
            )
        print(f"Pipeline run completed: {load_info}")
    except Exception as e:
        print(f"Error running pipeline: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run full or partial page load to BigQuery.")
    parser.add_argument('--from_date', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--to_date', type=str, help='End date (YYYY-MM-DD)')
    args = parser.parse_args()

    #defaults
    today = datetime.now()
    default_from = today - timedelta(days=8)  # Default to 8 days ago
    default_to = today - timedelta(days=1)  # Default to yesterday

    from_date = datetime.strptime(args.from_date, "%Y-%m-%d") if args.from_date else default_from
    to_date = datetime.strptime(args.to_date, "%Y-%m-%d") if args.to_date else default_to

    from_date_str = from_date.strftime("%Y-%m-%d")
    to_date_str = to_date.strftime("%Y-%m-%d")
    
    if from_date > to_date:
        raise ValueError("from_date cannot be after to_date")
    
    run_pipeline(from_date=from_date_str, to_date=to_date_str)
    