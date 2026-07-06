from pathlib import Path
import pandas as pd
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient



from qdrant_client.models import VectorParams,Distance,PointStruct

ROOT=Path(__file__).resolve().parents[3]
DOCS=ROOT/"data"/"processed"/"perfumes_docs.parquet"
STORE=ROOT/"qdrant_storage"
COLLECTION="perfumes"

MODEL_NAME="BAAI/bge-base-en-v1.5"

def as_list(x):
    return [] if x is None else list(x)

def main():
    df=pd.read_parquet(DOCS)
    print(f"loaded {len(df):,} docs")

    model=SentenceTransformer(MODEL_NAME,device="cuda")
    dim=model.get_sentence_embedding_dimension()

    vectors=model.encode(df["document"].tolist(),batch_size=64,show_progress_bar=True,normalize_embeddings=True,)
    client=QdrantClient(path=str(STORE))
    if client.collection_exists(COLLECTION):
        client.delete_collection(COLLECTION)

    client.create_collection(collection_name=COLLECTION,vectors_config=VectorParams(size=dim,distance=Distance.COSINE),)

    def payload(r): 
        return {
            "pid": r["id"], "name": r["name"], "brand": r["brand"],
            "family": r["family"], "gender": r["gender"],
            "longevity": float(r["longevity"]),
            "projection": float(r["projection"]),
            "climate_hot_humid": float(r["climate_hot_humid"]),
            "accords": as_list(r["accords"]),
            "notes_all": as_list(r["notes_all"]),
            "rating": (None if pd.isna(r["rating"]) else float(r["rating"])),
            "url": r.get("url", ""), "document": r["document"],
        }   
    
    points=[PointStruct(id=i,vector=vectors[i].tolist(),payload=payload(df.iloc[i]))
            for i in range(len(df))]
    

    B=512
    for s in range(0,len(points),B):
        client.upsert(collection_name=COLLECTION,points=points[s:s+B])
    print(f"indexed {len(points):,} into '{COLLECTION}' at {STORE}")  
    ##test
    q="fresh citrus summer scent for hot,humid weather,long lasting" 
    qv=model.encode([q],normalize_embeddings=True)[0].tolist()
    hits = client.query_points(collection_name=COLLECTION, query=qv, limit=5).points
    print("\n top hits for",q)
    for h in hits:
        p=h.payload
        print(f"{h.score:.3f}  {p['name']} — {p['brand']} [{p['family']}] "
              f"climate={p['climate_hot_humid']}")
        
if __name__=="__main__":
    main()
