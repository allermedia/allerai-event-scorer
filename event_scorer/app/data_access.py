import time
import pandas as pd
from google.cloud import bigquery
import json
from google.cloud import secretmanager
from google.oauth2 import service_account
import os
import google.auth
import traceback


# Module-level globals for cache and timestamps
_cached_articles = None
_cached_tag_scores = None
_last_refresh = 0

class DataManager:
    def __init__(self, refresh_interval_seconds=3600):
        self.refresh_interval = refresh_interval_seconds
        
        credentials, self.project_id = google.auth.default()
        self.client = bigquery.Client()
        self.client_articles, self.articles_project_id = self.get_source_client(self.project_id)

    def _fetch_articles(self) -> pd.DataFrame:
        sql = f"""
        WITH ranked_articles AS (
        SELECT 
            page_id as article_id, 
            site_domain, 
            main_category,
            category,
            sub_category,
            text_embeddings_en as embeddings_en,
            ROW_NUMBER() OVER (PARTITION BY site_domain ORDER BY published_ts DESC) AS rn
        FROM `{self.articles_project_id}.editorial.pages`
        WHERE page_type = 'Article'
        AND text_embeddings_en IS NOT NULL
        )
        SELECT 
        article_id, 
        site_domain, 
        main_category, 
        category, 
        sub_category, 
        embeddings_en
        FROM ranked_articles
        WHERE rn <= 50
        """
        print("Fetching articles...")
        query_job = self.client_articles.query(sql)
        df = query_job.result().to_dataframe()
        print(f"Fetched {len(df)} articles")
        df = self.validate_embeddings_column(df)
        return df

    def _fetch_tag_scores(self) -> pd.DataFrame:
        sql = f"""
        SELECT * FROM `{self.project_id}.nordic_tag_scores.tag_scores`
        WHERE TRUE
        LIMIT 1
        """
        print("Fetching tag scores...")
        query_job = self.client.query(sql)
        df = query_job.result().to_dataframe()
        print(f"Fetched {len(df)} rows from tag_scores")
        return df

    def refresh_cache(self):
        global _cached_articles, _cached_tag_scores, _last_refresh
        try:
            print("Refreshing cache for all tables...")
            _cached_articles = self._fetch_articles()
            _cached_tag_scores = self._fetch_tag_scores()
            _last_refresh = time.time()
            print(f"Cache refreshed at {time.ctime(_last_refresh)}")
        except Exception as e:
            print("Exception during cache refresh:", e)
            print(traceback.format_exc())
            raise


    def get_dataframes(self):
        global _cached_articles, _cached_tag_scores, _last_refresh
        try:
            now = time.time()
            if (_cached_articles is None or _cached_tag_scores is None
                    or (now - _last_refresh) > self.refresh_interval):
                print("Cache stale or empty. Refreshing cache...")
                self.refresh_cache()
            else:
                print("Using cached dataframes")
            return {
                "articles": _cached_articles.copy() if _cached_articles is not None else None,
                "tag_scores": _cached_tag_scores.copy() if _cached_tag_scores is not None else None,
            }
        except Exception as e:
            print("Exception during get_dataframes:", e)
            print(traceback.format_exc())
            raise

    def validate_embeddings_column(self, df: pd.DataFrame) -> pd.DataFrame:
        def safe_pass(x):
            if isinstance(x, list) and all(isinstance(i, (float, int)) for i in x):
                return x
            return None

        df["embeddings_en"] = df["embeddings_en"].apply(safe_pass)
        return df

    def get_source_client(self, secret_project_id: str):
        secret_name = os.getenv("ADP_SECRET_NAME", "missing environment variable SECRET_NAME")
        if secret_name == "missing environment variable SECRET_NAME":
            raise ValueError("Environment variable 'ADP_SECRET_NAME' is not set.")
        
        client = secretmanager.SecretManagerServiceClient()
        secret_path = f"projects/{secret_project_id}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(request={"name": secret_path})
        secret_string = response.payload.data.decode("UTF-8")
        key_info = json.loads(secret_string)
        credentials = service_account.Credentials.from_service_account_info(key_info)
        source_project_id = key_info.get("project_id")
        bq_client = bigquery.Client(credentials=credentials, project=source_project_id)
        
        return bq_client, source_project_id
