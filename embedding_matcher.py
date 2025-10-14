import logging
from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

logger = logging.getLogger('HackBountyAgent.Matcher')

class EmbeddingMatcher:
    """
    Uses Sentence-BERT (SBERT) to perform semantic matching between a
    student's profile and event descriptions.
    """
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """Initializes the SBERT model."""
        logger.info(f"Loading SBERT model: {model_name}...")
        try:
            # SBERT provides high-quality sentence embeddings
            self.model = SentenceTransformer(model_name)
            logger.info("SBERT model loaded successfully.")
        except Exception as e:
            logger.critical(f"Failed to load SBERT model: {e}")
            self.model = None

    def _get_embedding(self, texts: List[str]) -> np.ndarray:
        """Generates embeddings for a list of texts."""
        if not self.model:
            return np.array([0]) # Return a dummy array if model failed to load
        
        # Generates embeddings (high-dimensional vectors)
        embeddings = self.model.encode(texts, convert_to_tensor=False)
        return embeddings

    def find_best_matches(
        self,
        student_profile: str,
        events: List[Dict[str, Any]],
        threshold: float
    ) -> List[Dict[str, Any]]:
        """
        Calculates the similarity between the student profile and each event
        description, filtering based on the threshold.
        """
        if not self.model or not events:
            logger.warning("Skipping matching due to missing model or no events.")
            return []

        # 1. Create a combined text for each event to represent its topic/focus
        event_texts = [
            f"Topic: {event['topic']}. Description: {event['description']}"
            for event in events
        ]
        
        # 2. Get embeddings for the student profile and all events
        texts_to_encode = [student_profile] + event_texts
        embeddings = self._get_embedding(texts_to_encode)
        
        # The first embedding is the student profile
        profile_embedding = embeddings[0].reshape(1, -1) 
        event_embeddings = embeddings[1:]

        # 3. Calculate Cosine Similarity
        # Cosine similarity measures the angle between two vectors (0 to 1)
        similarities = cosine_similarity(profile_embedding, event_embeddings)[0]
        
        matched_events = []
        
        # 4. Filter and annotate events
        for i, (event, score) in enumerate(zip(events, similarities)):
            event['similarity_score'] = round(score, 4)
            
            if score >= threshold:
                # Basic eligibility filter (a production system would use regex or a separate LLM call)
                if 'university students' in event['eligibility'].lower() and 'junior' in student_profile.lower():
                    event['eligibility_ok'] = True
                    matched_events.append(event)
                elif 'open to all' in event['eligibility'].lower():
                    event['eligibility_ok'] = True
                    matched_events.append(event)
                else:
                    event['eligibility_ok'] = False
                    logger.info(f"Filtered {event['title']} (Score: {score}) due to eligibility mismatch.")
            else:
                logger.info(f"Filtered {event['title']} (Score: {score}) below threshold {threshold}.")

        logger.info(f"Matching complete. Found {len(matched_events)} highly relevant events.")
        return matched_events
