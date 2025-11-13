from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import numpy as np
import traceback

class SimilarityScorer:
    def __init__(self):
        pass

    def embedding_relevance(self, df_event: pd.DataFrame, df_articles: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
        try:
            event_id = df_event["article_id"].iloc[0]
            event_embedding = np.array(df_event["embeddings_en"].iloc[0], dtype=np.float32)

            valid_articles = df_articles.dropna(subset=["embeddings_en"]).copy()
            valid_articles = valid_articles[valid_articles["embeddings_en"].map(lambda x: len(x) > 0)]

            if valid_articles.empty:
                raise ValueError("No valid articles found with non-empty embeddings")

            results = []
            grouped_articles = valid_articles.groupby("site_domain")

            for site, candidates in grouped_articles:
                candidate_embeddings = [np.array(e, dtype=np.float32) for e in candidates["embeddings_en"]]

                df_sims = self.compute_cosine_similarity(
                    event_embedding,
                    candidate_embeddings,
                    candidates["article_id"].tolist(),
                    candidates["site_domain"].tolist()
                )

                top_scores_mean = df_sims.nlargest(top_n, "embedding_similarity")["embedding_similarity"].mean()

                results.append({
                    "id": event_id,
                    "site_domain": site,
                    "embedding_similarity": top_scores_mean
                })

            if not results:
                raise ValueError(f"No similarity scores computed for event_id {event_id}")

            return pd.DataFrame(results)

        except Exception as e:
            traceback.print_exc()
            raise

    def compute_cosine_similarity(self, event_embedding: np.ndarray, candidate_embeddings: list, candidate_article_ids: list, candidate_sites: list) -> pd.DataFrame:
        sims = cosine_similarity(
            event_embedding.reshape(1, -1),
            np.vstack(candidate_embeddings)
        )[0]

        return pd.DataFrame({
            "article_id": candidate_article_ids,
            "site_domain": candidate_sites,
            "embedding_similarity": sims
        })
