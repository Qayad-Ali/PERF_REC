# eval/run_eval.py
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from perfrec.retrieve.search import search
from perfrec.retrieve.rerank import rerank

ROOT   = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "eval" / "golden_set.jsonl"
K = 6

def as_set(x):
    return None if x is None else set(x if isinstance(x, list) else [x])

def family_prec(payloads, fams):
    if not fams or not payloads: return None
    return round(sum(1 for p in payloads if p["family"] in fams) / len(payloads), 2)

def evaluate():
    rows = [json.loads(l) for l in open(GOLDEN, encoding="utf-8") if l.strip()]
    dense_s, rerank_s, filt = [], [], []
    for r in rows:
        fams = as_set(r.get("expect_family"))
        mc, ml = r.get("min_climate"), r.get("min_longevity")

        dense    = search(r["query"], min_climate=mc, min_longevity=ml, limit=K,use_rerank=False)      # top-6 direct
        pool     = search(r["query"], min_climate=mc, min_longevity=ml, limit=20,use_rerank=False)     # top-20...
        reranked = rerank(r["query"], pool, top_k=K)                                   # ...reranked to 6

        dp = family_prec([h.payload for h in dense], fams)
        rp = family_prec([h.payload for h in reranked], fams)
        if dp is not None: dense_s.append(dp)
        if rp is not None: rerank_s.append(rp)
        if mc is not None and dense:
            filt.append(1.0 if all(h.payload["climate_hot_humid"] >= mc for h in dense) else 0.0)

        print(f"{r['query'][:44]:44} | dense={dp}  rerank={rp}")

    mean = lambda x: round(sum(x)/len(x), 3) if x else None
    print(f"\n=== ABLATION: family precision@{K} ===")
    print(f"dense retrieval:        {mean(dense_s)}")
    print(f"dense + cross-encoder:  {mean(rerank_s)}")
    print(f"climate-filter correct: {mean(filt)}  (should be 1.0)")

if __name__ == "__main__":
    evaluate()
