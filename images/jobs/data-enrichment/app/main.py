from langchain_openai import OpenAIEmbeddings
from data_access import DataAccess
import google.auth
import os

def run_pipeline():    
    print("Running pipeline...")
    credentials, project_id = google.auth.default()

    openai_api_key = os.environ.get('OPENAI_API_KEY', 'Missing environment variable')

    drafts_source_table = f"{project_id}.platform_drafts.drafts_modelled"
    drafts_target_table = f"{project_id}.platform_drafts.drafts_enriched"
    pages_source_table = f"{project_id}.adp_pages.pages"
    pages_target_table = f"{project_id}.adp_pages.pages_enriched"

    da = DataAccess()
    drafts = da.get_drafts(drafts_source_table, drafts_target_table)
    pages = da.get_pages(pages_source_table, pages_target_table)

    drafts = da.normalize_text_column(drafts, 'content', 'content_normalized')
    pages = da.normalize_text_column(pages, 'bodytext', 'bodytext_normalized')

    embedder = OpenAIEmbeddings(
        model="text-embedding-3-small", 
        dimensions=512, 
        openai_api_key=openai_api_key
    )

    da.embed_and_store(drafts, 'content_normalized', 'drafts', embedder, da, drafts_target_table)
    da.embed_and_store(pages, 'bodytext_normalized', 'pages', embedder, da, pages_target_table)

if __name__ == "__main__":
    run_pipeline()
