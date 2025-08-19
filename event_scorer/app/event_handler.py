from flask import jsonify
import sys
sys.path.append('./models')
from features.similarity import SimilarityScorer
from features.classification import ClassificationScorer
from features.tags import TagScorer
from features.potential import PotentialScorer
from scoring.scoring_weighted import Scorer
from data_access import DataManager
from parsers import RequestParser
from pubsub import PubSubService
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class EventHandler:
    def __init__(self, project_id: str, output_topic: str, output_topic_error_log: str):
        self.data_manager = DataManager()
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

            dfs = self.data_manager.get_dataframes()
            df_articles = dfs["articles"]
            df_tag_scores = dfs["tag_scores"]
            df_traffic = dfs["traffic"]

            df_articles = df_articles.merge(
                df_traffic[['article_id', 'site_domain', 'pageviews_first_7_days']],
                on=['article_id', 'site_domain'],
                how='left'
            )

            potential_scores = self.potential_scorer.predict_classification(df_event, df_articles)

            logger.info(f"Scoring article_id: {df_event['article_id'].iloc[0]}...")

            similarity_scores = self.similarity_scorer.embedding_relevance(df_event, df_articles)
            classification_scores = self.classification_scorer.category_relevance(df_event, df_articles)
            tag_scores = self.tag_scorer.tag_relevance(df_event, df_tag_scores)

            combined_scores = (
                similarity_scores
                .merge(classification_scores, on=["id", "site_domain"], how="inner")
                .merge(tag_scores, on=["id", "site_domain"], how="left")
            )
            combined_scores["tag_score"] = combined_scores["tag_score"].fillna(0)

            logger.info("\n%s", combined_scores.to_string(index=False))

            logger.info(combined_scores[["embedding_similarity", "category_similarity", "tag_score"]].dtypes)

            scores = self.scorer.compute_weighted_score(combined_scores)

            final = scores.merge(
                potential_scores[['id', 'site_domain', 'potential_quartile', 'pageview_range']],
                on=['id', 'site_domain'],
                how='left'
            )

            payload = final.to_dict(orient="records")

            self.pubsub_service.publish(payload, attributes)

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
    