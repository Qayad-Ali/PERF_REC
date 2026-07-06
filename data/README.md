# Data

Raw datasets are **not** committed (licensing + size). Run `python scripts/download_data.py` to populate `raw/`.

## Layout
- `raw/` — downloaded datasets, untouched (gitignored)
  - `parfumo/parfumo_data_clean.csv` — primary base table, from R's TidyTuesday (2024-12-10) GitHub mirror; ~59k perfumes, no login
  - `fragrantica/` — optional review corpus, Kaggle `olgagmiufana1/fragrantica-com-fragrance-dataset` (needs Kaggle token + accepted terms)
  - FragDB is NOT used — its full bundle is paid; the free repo is samples only.
- `interim/` — normalized / cleaned intermediates (gitignored)
- `processed/` — canonical, embedding-ready records (gitignored)

## Provenance & ethics
- All community data (accords, ratings, reviews) is **opinion**, kept separate from brand-declared notes.
- Sourced from published datasets — **not** scraped from Fragrantica (its ToS prohibits scraping).
- Attribute sources in the top-level README; do not republish proprietary content verbatim.
