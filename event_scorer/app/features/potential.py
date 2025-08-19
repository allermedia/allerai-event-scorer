import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import ast

class PotentialScorer:
    
    def predict_classification(self, df_events, df_articles, N=25):
        df_articles = df_articles.dropna(subset=['pageviews_first_7_days'])
        
        site_quartiles = df_articles.groupby('site_domain')['pageviews_first_7_days'].quantile([0.25, 0.5, 0.75]).unstack()
        site_quartiles.columns = ['Q1', 'Q2', 'Q3']
        
        df_articles = df_articles.dropna(subset=["embeddings_en"]).copy()

        article_embeddings = np.array(df_articles['embeddings_en'].tolist())
        
        all_predictions = []
        
        for _, event in df_events.iterrows():
            new_embedding = np.array(event['embeddings_en']).reshape(1, -1)
            similarities = cosine_similarity(new_embedding, article_embeddings).flatten()
            
            df_articles['similarity_score'] = similarities
            top_similar = (
                df_articles.sort_values(['site_domain', 'similarity_score'], ascending=[True, False])
                .groupby('site_domain')
                .head(N)
            )
            
            predictions = self._classify_article(event['article_id'], top_similar, site_quartiles)
            all_predictions.append(predictions)
        
        return pd.concat(all_predictions, ignore_index=True)
    
    
    def _classify_article(self, article_id, similar_articles, site_quartiles):
        results = []
        
        for site, site_articles in similar_articles.groupby('site_domain'):
            std = site_articles['pageviews_first_7_days'].std()
            median = site_articles['pageviews_first_7_days'].median()
            calc = std - median * 2
            
            # Compute weighted pageviews vectorized
            conditions = [
                site_articles['pageviews_first_7_days'] > std,
                (site_articles['pageviews_first_7_days'] <= std) & (site_articles['pageviews_first_7_days'] > calc),
                site_articles['pageviews_first_7_days'] <= calc
            ]
            freqs = [cond.sum() for cond in conditions]
            weights = [f / len(site_articles) for f in freqs]
            
            site_articles['weighted_page_views'] = np.select(
                conditions,
                [site_articles['pageviews_first_7_days'] * w for w in weights]
            )
            
            median_weighted = site_articles['weighted_page_views'].median()
            
            # Determine closest quartile
            Q1, Q2, Q3 = site_quartiles.loc[site]
            quartile_diffs = [abs(median_weighted - Q1), abs(median_weighted - Q2), abs(median_weighted - Q3)]
            closest = np.argmin(quartile_diffs) + 1  # 1-based index
            
            if closest == 1:
                iq_dist = Q2 - Q1
                q_range = [int(Q1 - 0.25 * iq_dist), int(Q1 + 0.25 * iq_dist)]
            elif closest == 2:
                iq_dist = Q3 - Q1
                q_range = [int(Q2 - 0.25 * iq_dist), int(Q2 + 0.25 * iq_dist)]
            else:
                iq_dist = Q3 - Q2
                q_range = [int(Q3 - 0.25 * iq_dist), int(Q3 + 0.25 * iq_dist)]
            
            results.append({
                'id': article_id,
                'site_domain': site,
                'potential_quartile': closest,
                'pageview_range': q_range
            })
        
        return pd.DataFrame(results)
