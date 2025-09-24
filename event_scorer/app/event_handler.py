from flask import jsonify
import sys
sys.path.append('./models')
from features.similarity import SimilarityScorer
from features.classification import ClassificationScorer
from features.tags import TagScorer
from features.potential import PotentialScorer
from scoring.scoring_weighted import Scorer
from platform_push import platform_push
from data_access import DataManager
from parsers import RequestParser
from pubsub import PubSubService
from typing import Any, Dict
import pandas as pd
import numpy as np
import logging
import tldextract

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class EventHandler:
    def __init__(self, project_id: str, output_topic: str, output_topic_error_log: str, adp_project_id: str):
        self.data_manager = DataManager(adp_project_id)
        self.similarity_scorer = SimilarityScorer()
        self.classification_scorer = ClassificationScorer()
        self.tag_scorer = TagScorer()
        self.potential_scorer = PotentialScorer()
        self.scorer = Scorer()
        self.request_parser = RequestParser()
        self.pubsub_service = PubSubService(project_id, output_topic)
        self.pubsub_service_error_log = PubSubService(project_id, output_topic_error_log)

    def process_request(self, request):
        payload = None
        message_id = None
        attributes = {}

        try:
            payload, attributes, message_id = self.request_parser.parse_request(request)

            if payload is None:
                return jsonify({"status": "error", "reason": "Invalid JSON payload"}), 400
        
            df_event = self.request_parser.payload_to_df(payload)

            # Get stored data
            dfs = self.data_manager.get_dataframes()
            df_articles = dfs["articles"]
            df_tag_scores = dfs["tag_scores"]
            df_traffic = dfs["traffic"]

            df_articles = df_articles.merge(
                df_traffic[['article_id', 'site_domain', 'pageviews_first_7_days']],
                on=['article_id', 'site_domain'],
                how='left'
            )

            # Score event
            logger.info(f"Scoring article_id: {df_event['article_id'].iloc[0]}, for domain {df_event['site_domain']}...")
            potential_scores = self.potential_scorer.predict_classification(df_event, df_articles)
            similarity_scores = self.similarity_scorer.embedding_relevance(df_event, df_articles)
            classification_scores = self.classification_scorer.category_relevance(df_event, df_articles)
            tag_scores = self.tag_scorer.tag_relevance(df_event, df_tag_scores)


            # Combine scores and compute final weighted score
            combined_scores = (
                similarity_scores
                .merge(classification_scores, on=["id", "site_domain"], how="inner")
                .merge(tag_scores, on=["id", "site_domain"], how="left")
            )

            combined_scores["tag_score"] = combined_scores["tag_score"].fillna(0)

            scores = self.scorer.compute_weighted_score(combined_scores)
            final = scores.merge(
                potential_scores[['id', 'site_domain', 'potential_quartile', 'pageview_range']],
                on=['id', 'site_domain'],
                how='left'
            )

            # Format final output
            site_value = df_event["site_domain"].iloc[0]
            extracted = tldextract.extract(site_value)
            base_domain = f"{extracted.domain}.{extracted.suffix}" if extracted.domain and extracted.suffix else None

            final["id"] = base_domain + ":" + final["id"].astype(str)
            final["potential_quartile"] = final["potential_quartile"].fillna(1)
            final['pageview_range'] = final['pageview_range'].apply(self.fill_nan_list)

            payload = final.to_dict(orient="records")

            # Publish to Pub/Sub
            self.pubsub_service.publish(payload, attributes)

            # Push to AI Platform
            platform_push(final)

            logger.info(f"Published scores for article_id: {df_event['article_id'].iloc[0]}")
            return jsonify({"status": "success"}), 200      
        
        except Exception as e:   
            logger.error(f"Error: {e}")         
            error_log = self.error_formatter(payload, message_id, e)            
            self.pubsub_service_error_log.publish(error_log, attributes)
            return jsonify({"error": str(e)}), 202
    
    def error_formatter(self, payload: Dict[str, Any], message_id: str, e: Exception) -> Dict[str, Any]:
        try:
            article_id = payload.get("article_id") if payload else None
        except (AttributeError, KeyError):
            article_id = None

        error_log = {
            "message_id": message_id or None,
            "article_id": article_id,
            "error": str(e)
        }
        return error_log
    
    def fill_nan_list(self, x):
        if x is None:
            return [0, 1]
        if isinstance(x, float) and np.isnan(x):
            return [0, 1]

        if isinstance(x, np.ndarray):
            x = x.tolist()

        if isinstance(x, list) and len(x) == 2:
            min_val = max(0, x[0]) 
            max_val = max(1, x[1]) 
            return [min_val, max_val]
        
        return x
