import time
import pandas as pd
from google.cloud import bigquery
import json
from google.cloud import secretmanager
from google.oauth2 import service_account
import os
import google.auth
import traceback
import numpy as np


class DataManager:
    def __init__(self, refresh_interval_seconds: int = 3600):
        self.refresh_interval = refresh_interval_seconds
        
        credentials, self.project_id = google.auth.default()
        self.client = bigquery.Client()
        self.client_articles, self.articles_project_id = self.get_source_client(self.project_id)

        self._cached_articles: pd.DataFrame | None = None
        self._cached_tag_scores: pd.DataFrame | None = None
        self._last_refresh: float = 0

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
        query_job = self.client_articles.query(sql)
        df = query_job.result().to_dataframe()
        df = self.validate_embeddings_column(df)
        return df

    def _fetch_tag_scores(self) -> pd.DataFrame:
        sql = f"""
        SELECT * FROM `{self.project_id}.nordic_tag_scores.tag_scores`
        WHERE TRUE
        LIMIT 1
        """
        query_job = self.client.query(sql)
        df = query_job.result().to_dataframe()
        return df

    def refresh_cache(self) -> None:
        try:
            self._cached_articles = self._fetch_articles()
            self._cached_tag_scores = self._fetch_tag_scores()
            self._last_refresh = time.time()
        except Exception:
            traceback.print_exc()
            raise

    def get_dataframes(self) -> dict[str, pd.DataFrame | None]:
        try:
            now = time.time()
            if (self._cached_articles is None or self._cached_tag_scores is None
                    or (now - self._last_refresh) > self.refresh_interval):
                self.refresh_cache()
            return {
                "articles": self._cached_articles.copy() if self._cached_articles is not None else None,
                "tag_scores": self._cached_tag_scores.copy() if self._cached_tag_scores is not None else None,
            }
        except Exception:
            traceback.print_exc()
            raise

    def validate_embeddings_column(self, df: pd.DataFrame) -> pd.DataFrame:
        def safe_pass(x):
            if isinstance(x, np.ndarray) and x.dtype in [np.float32, np.float64] and x.size > 0:
                return x
            return None

        df["embeddings_en"] = df["embeddings_en"].apply(safe_pass)
        return df

    def get_source_client(self, secret_project_id: str):
        secret_name = os.getenv("ADP_SECRET_NAME")
        if not secret_name:
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
