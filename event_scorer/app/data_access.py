import time
import threading
import pandas as pd
from google.cloud import bigquery
import json
from google.cloud import secretmanager
from google.oauth2 import service_account
import os
import google.auth

class DataManager:
    def __init__(self, refresh_interval_seconds=3600):
        self.refresh_interval = refresh_interval_seconds
        self.cache = {
            "articles": None,
            "tag_scores": None,
        }
        self.last_refresh = 0
        self.lock = threading.Lock()
        self.client = bigquery.Client()
        
        credentials, self.project_id = google.auth.default()
        self.client_articles, self.articles_project_id = self.get_source_client(self.project_id)
        
        threading.Thread(target=self.refresh_cache, daemon=True).start()
        
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
        with self.lock:
            print("Refreshing cache for all tables...")
            self.cache["articles"] = self._fetch_articles()
            self.cache["tag_scores"] = self._fetch_tag_scores()
            self.last_refresh = time.time()
            print(f"Cache refreshed at {time.ctime(self.last_refresh)}")

    def get_dataframes(self):
        with self.lock:
            now = time.time()
            if any(df is None for df in self.cache.values()) or (now - self.last_refresh) > self.refresh_interval:
                print("Cache stale or empty. Refreshing cache...")
                self.refresh_cache()
            else:
                print("Using cached dataframes")
            return {k: v.copy() for k, v in self.cache.items()}
    
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