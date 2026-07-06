# src/perfrec/retrieve/search.py
from pathlib import Path
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range
from perfrec.retrieve.rerank import rerank
ROOT       = Path(__file__).resolve().parents[3]
STORE      = ROOT / "qdrant_storage"
COLLECTION = "perfumes"
MODEL_NAME = "BAAI/bge-base-en-v1.5"        # MUST match the index model
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

_model = None
def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME, device="cpu")
    return _model
_client = None
def _get_client():
    global _client
    if _client is None:
        _client = QdrantClient(path=str(STORE))
    return _client

def search(text, *, min_climate=None, gender=None, min_longevity=None, limit=6, use_rerank=True):
    qv = _get_model().encode([QUERY_PREFIX + text], normalize_embeddings=True)[0].tolist()

    must = []
    if min_climate is not None:
        must.append(FieldCondition(key="climate_hot_humid", range=Range(gte=min_climate)))
    if min_longevity is not None:
        must.append(FieldCondition(key="longevity", range=Range(gte=min_longevity)))
    if gender is not None:
        must.append(FieldCondition(key="gender", match=MatchValue(value=gender)))
    flt = Filter(must=must) if must else None

    client = _get_client()
    fetch = max(limit, 20) if use_rerank else limit          # bigger pool to rerank from
    hits = client.query_points(collection_name=COLLECTION, query=qv,
                               query_filter=flt, limit=fetch).points
    if use_rerank and hits:
        hits = rerank(text, hits, top_k=limit)               # cross-encoder → top `limit`

    for h in hits:
        p = h.payload
        print(f"{h.score:.3f}  {p['name']} — {p['brand']} [{p['family']}] "
              f"climate={p['climate_hot_humid']} long={p['longevity']} gender={p['gender']}")
    return hits

_client = None
def _get_client():
    global _client
    if _client is None:
        _client = QdrantClient(path=str(STORE))
    return _client
if __name__ == "__main__":
    print("--- unfiltered ---")
    search("something compliment-worthy for the office")
    print("\n--- Delhi hot+humid, must be climate-fit AND long lasting ---")
    search("something compliment-worthy for the office", min_climate=0.7, min_longevity=0.7)
