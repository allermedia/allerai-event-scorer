import pandas as pd
import re

class TagScorer:
    def __init__(self):
        pass

    def tag_relevance(self, df_event: pd.DataFrame, df_entities: pd.DataFrame) -> pd.DataFrame:
        results = []

        df_entities = df_entities.copy()
        df_entities["tag"] = df_entities["tag"].astype(str).str.lower()
        bodytext = str(df_event.iloc[0]["bodytext"]).lower()
        doc_id = df_event.iloc[0]["article_id"]

        for site, site_entities in df_entities.groupby("site"):
            site_entities = site_entities.assign(
                matched=site_entities["tag"].apply(lambda t: t in bodytext)
            )

            matched = site_entities[site_entities["matched"]]

            if not matched.empty:
                matched_tags = matched["tag"].tolist()
                scores = (matched["frequency"] / matched["max_frequency"]).tolist()
                results.append({
                    "id": doc_id,
                    "site_domain": site,
                    "tag_score": max(scores),
                    "entities": matched_tags
                })
            else:
                results.append({
                    "id": doc_id,
                    "site_domain": site,
                    "tag_score": 0.0,
                    "entities": []
                })

        return pd.DataFrame(results)
    