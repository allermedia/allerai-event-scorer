import dlt
from draft_fetcher import get_drafts

def run_pipeline():
    pipeline = dlt.pipeline(
        pipeline_name="mongo_to_bq_incremental",
        destination="bigquery",
        dataset_name="platform_drafts"
    )

    print("Running pipeline...")

    try:
        load_info = pipeline.run(
            get_drafts(),
            write_disposition="merge"
            )
        print(f"Pipeline run completed: {load_info}")
    except Exception as e:
        print(f"Error running pipeline: {e}")

if __name__ == "__main__":
    run_pipeline()
    