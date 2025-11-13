from scipy.spatial.distance import cosine
import pandas as pd
from tqdm import tqdm

class MatchingService():

    def __init__(self):
        print("MatchingService initialized")

    def label_confidence(self, similarity) -> str:
        """        
        Label the confidence level based on the similarity score.
        """
        if similarity >= 0.95:
            return "very_high"
        elif similarity >= 0.90:
            return "high"
        elif similarity >= 0.85:
            return "medium"
        elif similarity >= 0.80:
            return "low"
        else:
            return "very_low"

    def cosine_similarity(self, v1, v2) -> float:
        """        
        Calculate cosine similarity between two vectors.
        """
        if v1 is None or v2 is None or len(v1) == 0 or len(v2) == 0 or len(v1) != len(v2):
            return 0.0
        
        return 1 - cosine(v1, v2)

    def create_matches_from_candidates(self, candidate_pairs: pd.DataFrame) -> pd.DataFrame:
        """
        Create matches from candidate pairs by finding the best match for each published page.
        """
        print('Creating matches from candidate pairs...')
        matches = []
        grouped = candidate_pairs.groupby('page_id')  

        for pub_id, group in tqdm(grouped, desc="Finding best matches"):
            # Compute cosine similarity for all rows in the group
            similarities = group.apply(
                lambda row: self.cosine_similarity(row['embedding_draft'], row['embedding_published']),
                axis=1
            )

            best_idx = similarities.idxmax()
            best_match = group.loc[best_idx]
            best_similarity = similarities[best_idx]
            decayed_score = best_similarity * best_match['time_decay']

            matches.append({
                'published_article_id': pub_id,
                'published_text': best_match['bodytext'],
                'citation_story_id': best_match['id_x'],
                'draft_text': best_match['content'],
                'time_decay': best_match['time_decay'],
                'decayed_score': decayed_score,
                'decayed_confidence_level': self.label_confidence(decayed_score),
                'similarity': best_similarity,
                'confidence_level': self.label_confidence(best_similarity),
                'created_by_match': int(best_match['full_name_lc'] == best_match['created_by_lc']),
                'created_at': best_match['created_at_dt'],
                'published_at': best_match['published_dt'],
                'site': best_match['site'],
                'radar_source': best_match['radar_source_id'],
            })

        return pd.DataFrame(matches)
    