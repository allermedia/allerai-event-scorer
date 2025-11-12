from data_access import DataAccess
from candidate_generation import CandidateGeneration
from matching import MatchingService
from datetime import datetime, timedelta
import argparse
import google.auth

def run_pipeline(from_date=None, to_date=None, draft_from_date=None):   
    print("Running pipeline...") 

    credentials, project_id = google.auth.default()

    # Set source and target tables for data retrieval and storage
    drafts_source_table = f"{project_id}.platform_drafts.drafts_enriched"
    pages_source_table = f"{project_id}.adp_pages.pages_enriched"
    users_source_table = f"{project_id}.platform_users.users"
    
    target_table = f"{project_id}.platform_match.pages_matched"

    # Retrieve data from BigQuery (platform drafts, published pages, and platform users)
    da = DataAccess()
    drafts = da.get_drafts(drafts_source_table, draft_from_date, to_date)
    pages = da.get_pages(pages_source_table, target_table, from_date, to_date)
    users = da.get_platform_users(users_source_table)

    # Merge drafts and users dataframes and preprocess drafts and pages
    cg = CandidateGeneration()
    pages_cleaned, drafts_cleaned = cg.data_preparation(pages, drafts, users)

    # Create candidates by matching drafts and pages on site, creator/author and created/published date)
    candidate_pairs = cg.create_candidate_pairs(pages_cleaned, drafts_cleaned)
        
    if candidate_pairs.empty:
        print("No candidate pairs found, stopping...")
        return
    
    # Compute matches from candidate pairs
    ms = MatchingService()
    results = ms.create_matches_from_candidates(candidate_pairs)

    #Upload results to BigQuery
    results_cleaned = da.prepare_df_for_bigquery(results)
    da.bigquery_write(results_cleaned, target_table)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run full or partial page load to BigQuery.")
    parser.add_argument('--from_date', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--to_date', type=str, help='End date (YYYY-MM-DD)')
    args = parser.parse_args()

    #defaults
    today = datetime.now()
    default_from = today - timedelta(days=7)  # Default to 7 days ago
    default_to = today  # Default to today

    from_date = datetime.strptime(args.from_date, "%Y-%m-%d") if args.from_date else default_from
    to_date = datetime.strptime(args.to_date, "%Y-%m-%d") if args.to_date else default_to

    # Drafts from date is set to 14 days before the from_date(for pages) to get drafts created leading up the earliest page publishes
    draft_from_date = from_date - timedelta(days=14)
    
    if from_date > to_date:
        raise ValueError("from_date cannot be after to_date")

    run_pipeline(from_date=from_date, to_date=to_date, draft_from_date=draft_from_date)
    