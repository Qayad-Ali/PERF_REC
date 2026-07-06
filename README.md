# PerfRec 🌿

A climate-aware, layering-first perfume recommender built on RAG.

I collect perfume, and the "find your scent" tools online felt shallow. None of them reason about the weather where you live or how to *layer* two scents. So I built PerfRec: type your situation in plain English (*"Delhi, hot and humid, office, want compliments"*) and get grounded recommendations plus layering combinations from ~21k fragrances. It runs locally with a local LLM, so no API keys or cloud costs.

## What it does

- **Recommends single scents** Filter the data with your query with semantic search.
- **Suggests layering pairs** (a fresh "lifter" over a long-lasting "anchor") with a spray ratio and application tips.
-**Climate aware response** works on weather Api to check the climate of the particular city mentioned.

## How it works

RAG pipeline with a small agent layer on top:

- **Retrieve** — fragrances are embedded (sentence-transformer) and stored in Qdrant. Climate is a **hard payload filter**, not a ranking nudge: in humid weather, cloying scents are dropped from the candidate set entirely.
- **Rerank** — over-fetch top 20, then a cross-encoder reranks to the best 6 (this lifted family precision 0.76 → 0.83).
- **Generate** — a local LLM writes the answer from *only* the retrieved candidates and cites real notes, so it can't invent perfumes.
- **Agent** — a planner routes the request (single / layering / both), calls tools (climate resolver, search, layering engine), and **self-corrects**: if the filter leaves too few results, it loosens and retries.
- **Layering engine** — pulls two pools (lifters + anchors) and scores every pair on role complementarity, fragrance-wheel harmony, shared-accord "bridge," climate fit, and a bonus for matching known layering recipes (e.g. citrus + woody).

## Results

15-query golden set, family precision on the top 6:

| Setup | Family precision@6 | Climate-filter correctness |
|---|---|---|
| Dense retrieval | 0.756 | 1.0 |
| Dense + cross-encoder rerank | **0.833** | 1.0 |

## Project structure

```
src/perfrec/
  ingest/      raw data → canonical parquet
  enrich/      derive family, longevity, projection, climate scores
  embed/       build embeddable documents
  index/       embed + load into Qdrant
  retrieve/    vector search + climate filter + cross-encoder rerank
  generate/    grounded LLM recommendation
  layering/    anchor + lifter pairing engine
  agent/       planner → executor → composer
  schema/      canonical Perfume model
app/           Streamlit UI
eval/          golden set + eval harness
scripts/       data download
config/        config.yaml
```
## System Architecture
![architecture](C:\Users\QAYAD ALI\Claude\Projects\PERFREC\assets\architecture.png)
## Data

~21k fragrances I scraped from an online retailer (names, brands, notes, accords, gender, descriptions), with strong global and Middle-Eastern coverage. Longevity/projection/climate fit aren't in the source; I derive them from the note structure. Personal project, so the scraped data and scrapers are git-ignored and not redistributed. Only code is in this repo.

## Tech stack

- Embeddings: sentence-transformers (bge-base-en-v1.5)
- Vector DB: Qdrant (local, payload filtering)
- Reranker: cross-encoder (bge-reranker-base)
- LLM: Gemma via Ollama (OpenAI-compatible API, swappable)
- UI: Streamlit · Eval: custom golden-set harness

## Running it

```bash
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt

python src/perfrec/enrich/enrich.py
python src/perfrec/embed/build_documents.py
python src/perfrec/index/build_index.py

ollama pull gemma4:e2b-it-qat
python -m streamlit run app/streamlit_app.py
python eval/run_eval.py
```

## v2 upgrades

- Bigger library 
- a second source to compare declared notes 
-a company published and crowd percieved comparison between the same fragrances
- llama.cpp instead of Ollama for finer GPU control and speed
- A cleaner, more user-friendly UI
- Cohere Command R+ for context-aware, grounded inference
- and much more ,just stay tuned
---
