from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import numpy as np
import traceback

class EventScorer:
    def __init__(self):
        print("EventScorer initialized")
        
    def embedding_relevance(self, df_event, df_articles, top_n=10):
        try:
            event_id = df_event["article_id"].iloc[0]
            
            if "embeddings_en" not in df_event.columns:
                raise ValueError("Missing 'embeddings_en' in event payload.")

            event_embedding = df_event["embeddings_en"].iloc[0]

            if event_embedding is None or len(event_embedding) == 0:
                raise ValueError(f"Event embedding is null or empty for article_id {event_id}")

            event_embedding = np.array(event_embedding, dtype=np.float32)

            print(f"Original articles shape: {df_articles.shape}")
            print(df_articles.columns.tolist())
            print(df_articles.head(3))
            print("embeddings_en column types in df_articles:")
            print(df_articles["embeddings_en"].apply(type).value_counts())
            print("Sample embeddings:")
            print(df_articles["embeddings_en"].head(3).tolist())

            df_articles["embeddings_en"] = df_articles["embeddings_en"].map(lambda x: list(x) if x is not None else None)

            valid_articles = df_articles.dropna(subset=["embeddings_en"]).copy()
            valid_articles = valid_articles[valid_articles["embeddings_en"].map(
                lambda x: isinstance(x, (list, np.ndarray)) and len(x) > 0
            )]
            
            print(f"Valid articles shape: {valid_articles.shape}")

            if valid_articles.empty:
                raise ValueError("No valid articles found with non-empty embeddings")
            
            results = []
            grouped_articles = valid_articles.groupby("site_domain")

            for site, candidates in grouped_articles:
                candidate_embeddings = [np.array(e, dtype=np.float32) for e in candidates["embeddings_en"]]

                if not candidate_embeddings:
                    continue

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
                raise ValueError(f"No similarity scores computed for event_id {event_id}. Check if candidate embeddings were empty.")

            return pd.DataFrame(results)

        except Exception as e:
            print(f"Exception in embedding_relevance: {e}")
            traceback.print_exc()
            raise

    def compute_cosine_similarity(self, event_embedding, candidate_embeddings, candidate_article_ids, candidate_sites):
        sims = cosine_similarity(
            event_embedding.reshape(1, -1),
            np.vstack(candidate_embeddings)
        )[0]

        return pd.DataFrame({
            "article_id": candidate_article_ids,
            "site_domain": candidate_sites,
            "embedding_similarity": sims
        })