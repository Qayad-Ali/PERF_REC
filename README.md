# PerfRec 🌿

**A climate-aware, layering-first perfume recommender built on RAG.**

Most perfume "AI" is a shallow marketing quiz. PerfRec takes a free-form request —
*"I live in Delhi, it's hot and humid, I want compliments, and I'd like to layer two perfumes I own"* —
and returns grounded recommendations (single scents **and** layering combinations), tuned to your
climate and taste, with an explanation of *why*.

## What makes it different
- **Dual-source truth** — models what the brand *declares* is in the bottle separately from what the
  crowd *actually smells*, and treats their disagreement as a feature.
- **Climate-aware** — heat, humidity, and season change the recommendation, not just the copy.
- **Layering engine** — recommends *pairs* (with ratios + application tips), not just bottles.

## Architecture
`query understanding → hybrid retrieval (Qdrant, filtered) → cross-encoder rerank → grounded generation`,
with a small agentic loop for layering. See [`PerfRec-Project-Plan.md`](./PerfRec-Project-Plan.md) for the full design.

## Project layout
```
config/          # config.yaml
data/            # raw / interim / processed  (gitignored; see data/README.md)
scripts/         # download_data.py  (Phase 0)
src/perfrec/     # ingest · schema · ontology · enrich · embed · index · retrieve · generate · layering · api
notebooks/       # data profiling & experiments
eval/            # golden set + layering seed pairs
app/             # Streamlit demo
tests/
```

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # fill in KAGGLE_KEY, ANTHROPIC_API_KEY, etc.
python scripts/download_data.py
```

## Roadmap
0. **Data foundation** — acquire + profile + canonical schema  ← *you are here*
1. Grounded single-scent RAG + explanations
2. Climate-aware personalization
3. Layering engine
4. Feedback loop, eval, write-up

## Data & ethics
Built on published datasets (Parfumo, Fragrantica, FragDB), not scraped. Community data is treated as
opinion and kept separate from brand-declared facts. Sources attributed; raw data kept out of git.
