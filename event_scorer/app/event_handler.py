from flask import jsonify
import sys
sys.path.append('./models')
from models.similarity import SimilarityScorer
from models.classification import ClassificationScorer
from data_access import DataManager
from parsers import RequestParser
from pubsub import PubSubService
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class EventHandler:
    def __init__(self, project_id: str, output_topic: str):
        self.data_manager = DataManager()
        self.similarity_scorer = SimilarityScorer()
        self.classification_scorer = ClassificationScorer()
        self.request_parser = RequestParser()
        self.pubsub_service = PubSubService(project_id, output_topic)

    def process_request(self, request):
        try:
            payload, attributes = self.request_parser.parse_request(request)

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
                on="site_domain",
                how="inner"
            )

            payload = combined_scores.to_dict(orient="records")
                        
            self.pubsub_service.publish(payload, attributes)

            return jsonify({"status": "success"}), 202

        except ValueError as e:
            print(f"Bad request: {e}")
            return jsonify({"error": str(e)}), 400

        except Exception as e:
            print(f"Error processing message: {e}")
            return jsonify({"error": str(e)}), 500   
            