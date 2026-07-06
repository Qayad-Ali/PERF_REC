# src/perfrec/retrieve/rerank.py

from sentence_transformers import CrossEncoder

_reranker = None
def _get_reranker():
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder("BAAI/bge-reranker-base", max_length=512, device="cpu")
    return _reranker

def rerank(query, hits, top_k=6):
    if not hits:
        return hits
    pairs = [(query, h.payload["document"]) for h in hits]      # doc text is in payload
    scores = _get_reranker().predict(pairs)
    ranked = sorted(zip(scores, hits), key=lambda x: x[0], reverse=True)
    return [h for _, h in ranked[:top_k]]
