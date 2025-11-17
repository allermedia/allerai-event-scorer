import pandas as pd
from pandas import DataFrame
from google.cloud import bigquery
import unicodedata
import re
from typing import Optional

class DataAccess():
    def __init__(self):
        self.client = bigquery.Client()
      
    def get_pages(self, source_table, target_table) -> DataFrame:
        sql = f"""
            SELECT
                page_id,
                site_domain,
                market,
                cms_page_id,
                title,
                intro,
                bodytext,
                bodytext_html,
                tags,
                section,
                author,
                url,
                page_type,
                lock_status,
                published_local_dt,
                published_ts,
                updated_ts,
                created_ts,
                created_by,
                verticals
            FROM
              `{source_table}`
            WHERE
                page_id NOT IN(SELECT page_id FROM
                `{target_table}`)
        """ 
        query_job = self.client.query(sql)
        df = query_job.to_dataframe()
        return df
    
    def get_drafts(self, source_table, target_table) -> DataFrame:
        sql = f"""
            SELECT
                id,
                configuration_id,
                created_at,
                is_deleted,
                selected_draft_id,
                user_id,
                draft_id,
                content,
                radar_source_id
            FROM
              `{source_table}`
            WHERE
                id NOT IN(SELECT id FROM
                `{target_table}`)
        """ 
        query_job = self.client.query(sql)
        df = query_job.to_dataframe()
        return df


    def bigquery_write(self, df: DataFrame, target_table: str):
        job = self.client.load_table_from_dataframe(
            dataframe=df,
            destination=target_table,
            job_config=bigquery.LoadJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND
            )
        )
        job.result() 
        print(f"Inserted {job.output_rows} rows into {target_table}")

    def normalize_text_column(self, df: pd.DataFrame, column: str, new_column: str = None) -> pd.DataFrame:
        def normalize(text):
            if pd.isnull(text):
                return ""
            text = str(text)
            text = unicodedata.normalize("NFKD", text)
            text = text.encode("ascii", "ignore").decode("utf-8")
            text = text.lower()
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'[^a-z0-9\s]', ' ', text)
            text = re.sub(r'\s+', ' ', text)
            return text.strip()

        target_column = new_column or column
        df[target_column] = df[column].apply(normalize)
        return df

    def embed_and_store(self, df: pd.DataFrame, input_column: str, name: str, embedder, da, target_table) -> Optional[pd.DataFrame]:
        if df.empty:
            print(f"No new {name}")
            return None
        else:
            print(f"Retrieved new {name}")

        df['vector_input'] = df[input_column].fillna("")


        if not all(isinstance(item, str) for item in df['vector_input']):
            print(f"Some entries in '{name}' vector_input are not valid strings.")
            return None

        batch_size = 200
        full_df = []

        for start in range(0, len(df), batch_size):
            batch_df = df.iloc[start:start + batch_size].copy()
            texts = batch_df['vector_input'].tolist()
            embeddings = embedder.embed_documents(texts)
            batch_df['embedding'] = embeddings
            batch_df.drop(columns=['vector_input'], inplace=True)

            self.bigquery_write(batch_df, target_table)
            print(f"{name} embeddings created and written for rows {start} to {start + len(batch_df) - 1}")
            full_df.append(batch_df)
