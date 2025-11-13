import pandas as pd
import numpy as np
import traceback

class ClassificationScorer:
    def __init__(self):
        pass

    def category_relevance(self, df_event, df_articles) -> pd.DataFrame:
        event = df_event.iloc[0]
        event_id = event["article_id"]

        levels = ["main_category", "category", "sub_category"]

        results = []
        sites = df_articles["site_domain"].unique()

        for site in sites:
            site_df = df_articles[df_articles["site_domain"] == site]

            score = 0
            for level in levels:
                val = event[level]
                if pd.isna(val) or val in ["Other", ""]:
                    continue
                if val in site_df[level].values:
                    score += 1

            # Normalize total score (0-3) to desired range (e.g. 0.7 to 0.85)
            normalized_score = 0.7 + (score / 3) * (0.85 - 0.7)

            results.append({
                "id": event_id,
                "site_domain": site,
                "category_similarity": normalized_score
            })

        return pd.DataFrame(results)
    