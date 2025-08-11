from flask import jsonify
import sys
sys.path.append('./models')
from models.similarity import SimilarityScorer
from models.classification import ClassificationScorer
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
        self.request_parser = RequestParser()
        self.pubsub_service = PubSubService(project_id, output_topic)
        self.pubsub_service_error_log = PubSubService(project_id, output_topic_error_log)

    def process_request(self, request):
        payload = None
        message_id = None

        try:
            payload, attributes, message_id = self.request_parser.parse_request(request)

            if payload is None:
                return jsonify({"status": "error", "reason": "Invalid JSON payload"}), 400
            
            df_event = self.request_parser.payload_to_df(payload)

            dfs = self.data_manager.get_dataframes()
            df_articles = dfs["articles"]
            df_tag_scores = dfs["tag_scores"]

            print("Scoring event...")

            similarity_scores = self.similarity_scorer.embedding_relevance(df_event, df_articles)
            classification_scores = self.classification_scorer.category_relevance(df_event, df_articles)

            combined_scores = similarity_scores.merge(
                classification_scores,
                on=["id", "site_domain"],
                how="inner"
            )

            payload = combined_scores.to_dict(orient="records")
                        
            self.pubsub_service.publish(payload, attributes)

            return jsonify({"status": "success"}), 202      
            
        except ValueError as e:
            logger.error(f"ValueError: {e}")
            error_log = self.error_formatter(payload, message_id, e)            
            self.pubsub_service_error_log.publish(error_log)
            return jsonify({"error": str(e)}), 200
        
        except Exception as e:   
            logger.error(f"Error: {e}")         
            error_log = self.error_formatter(payload, message_id, e)            
            self.pubsub_service_error_log.publish(error_log)
            return jsonify({"error": str(e)}), 200
    
    def error_formatter(self, payload: Dict[str, Any], message_id: str, e: Exception) -> Dict[str, Any]:
        try:
            article_id = payload.get("article_id")
            if article_id is None:
                raise KeyError("article_id not found in payload")
        except (AttributeError, KeyError):
            article_id = None

        error_log = {
            "message_id": message_id,
            "article_id": article_id,
            "error": str(e)
        }

        return error_log