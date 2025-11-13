import pandas as pd
from pandas import DataFrame
from google.cloud import bigquery

class DataAccess():
    def __init__(self):
        self.client = bigquery.Client()
        print('DataAccess initialized')

    def get_pages(self, source_table, target_table, from_date, to_date) -> DataFrame:
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
                verticals,
                bodytext_normalized,
                embedding
            FROM
              `{source_table}`
            WHERE
                CAST(page_id AS STRING) NOT IN(SELECT published_article_id FROM `{target_table}`)
            AND 
                published_ts BETWEEN TIMESTAMP('{from_date}') AND TIMESTAMP('{to_date}')
        """ 
        query_job = self.client.query(sql)
        df = query_job.to_dataframe()
        return df

    def get_drafts(self, source_table, draft_from_date, to_date) -> DataFrame:
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
                radar_source_id,
                content_normalized,
                embedding
            FROM
              `{source_table}`
            WHERE
                created_at BETWEEN TIMESTAMP('{draft_from_date}') AND TIMESTAMP('{to_date}')
        """ 
        query_job = self.client.query(sql)
        df = query_job.to_dataframe()
        return df
        
    def get_platform_users(self, source_table) -> DataFrame:
        sql = f"""
            SELECT
                id,
                first_name,
                last_name
            FROM
              `{source_table}`
        """ 
        query_job = self.client.query(sql)
        df = query_job.to_dataframe()
        return df
        
    def prepare_df_for_bigquery(self, df: pd.DataFrame) -> pd.DataFrame:
        string_cols = [
            'published_article_id', 'published_text', 'citation_story_id', 'draft_text', 
            'decayed_confidence_level', 'confidence_level', 'site', 'radar_source'
        ]

        for col in string_cols:
            if col in df.columns:
                df[col] = df[col].fillna('').astype(str)

        df['created_at'] = pd.to_datetime(df['created_at'], utc=True)
        df['published_at'] = pd.to_datetime(df['published_at'], utc=True)

        df['created_at'] = df['created_at'].fillna(pd.Timestamp("1970-01-01", tz="UTC"))
        df['published_at'] = df['published_at'].fillna(pd.Timestamp("1970-01-01", tz="UTC"))

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
    