import numpy as np
import pandas as pd
from src.tools.base import get_cocktails_df
from src.utils.config import Config

_model = None
_cocktail_embeddings = None
_cocktail_texts = []

def get_transformer_model():
    """Lazily load the sentence-transformers model to save startup time."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        # Falls back to local cache or downloads to C:\\Users\\<user>\\.cache\\huggingface\\hub\\
        model_name = Config.EMBEDDING_MODEL or "all-MiniLM-L6-v2"
        print(f"Loading local SentenceTransformer model: {model_name} ...")
        _model = SentenceTransformer(model_name)
    return _model

def get_cocktail_embeddings():
    """Generate or retrieve cached cocktail vector embeddings."""
    global _cocktail_embeddings, _cocktail_texts
    df = get_cocktails_df()
    if df.empty:
        return np.array([]), []
        
    if _cocktail_embeddings is None:
        model = get_transformer_model()
        
        # Build representing text for each cocktail to capture name, categories, flavor profile, and story
        texts = []
        for _, row in df.iterrows():
            text_parts = [
                f"Name: {row.get('name', '')}",
                f"Category: {row.get('category', '')}",
                f"Flavor Profile: {row.get('flavor_profile', '')}",
                f"ABV Level: {row.get('abv_category', '')}",
                f"History and Vibe: {row.get('meaning_and_history', '')}",
                f"Instructions: {row.get('instructions', '')}"
            ]
            texts.append(". ".join(text_parts))
            
        _cocktail_texts = texts
        print(f"Embedding {len(texts)} cocktails ...")
        _cocktail_embeddings = model.encode(texts, show_progress_bar=False)
        
    return _cocktail_embeddings, _cocktail_texts

def semantic_search_cocktails(query: str, top_n: int = 5) -> list:
    """
    Computes cosine similarity between user query and all cocktails, returning ranked indices and scores.
    """
    if not query.strip():
        return []
        
    model = get_transformer_model()
    embeddings, texts = get_cocktail_embeddings()
    if len(embeddings) == 0:
        return []
        
    # Encode query
    query_emb = model.encode([query], show_progress_bar=False)[0]
    
    # Calculate cosine similarities
    # embeddings shape: (N, 384), query_emb shape: (384,)
    norms = np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query_emb)
    norms[norms == 0] = 1e-9 # Prevent division by zero
    similarities = np.dot(embeddings, query_emb) / norms
    
    # Sort indices by highest similarity score
    sorted_indices = np.argsort(similarities)[::-1]
    
    results = []
    for idx in sorted_indices[:top_n]:
        results.append({
            "index": int(idx),
            "score": float(similarities[idx])
        })
    return results
