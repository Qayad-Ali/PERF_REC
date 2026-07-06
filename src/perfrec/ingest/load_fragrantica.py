"""
Step 1 — Canonical loader.

Reads the raw Fragrantica `fra_cleaned.csv` and produces ONE clean, typed table
at data/processed/perfumes.parquet. The rest of the pipeline reads that file,
never the raw CSV again — that decoupling is why messy source data never leaks
into your engine.

What it does (the logic):
  1. read with the right params  (sep=';', latin-1, python engine, skip bad lines)
  2. de-duplicate on the perfume URL (one row per perfume)
  3. fix European decimals   ("1,42" -> 1.42)
  4. split notes/accords strings -> real lists (lowercased, de-noised, de-duped)
  5. validate every row through the Perfume schema (enforces the contract)
  6. quality gate: drop rows with no notes at all (useless for a notes-based recommender)
  7. write Parquet (preserves list columns + dtypes; loads fast)

Run from the repo root:
    python src/perfrec/ingest/load_fragrantica.py
"""
from __future__ import annotations

import re
import sys
import json
from pathlib import Path

import pandas as pd

# make the `perfrec` package importable no matter where you run this from
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # .../src
from perfrec.schema.perfume import Perfume  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]                    # repo root
RAW = ROOT / "data" / "raw" / "fragrantica" / "fra_cleaned.csv"
OUT = ROOT / "data" / "processed" / "perfumes.parquet"

ACCORD_COLS = ["mainaccord1", "mainaccord2", "mainaccord3", "mainaccord4", "mainaccord5"]
# tokens that are noise, not real notes/accords/perfumers
NOISE = {"", "unknown", "n/a", "na", "none", "-", "main accords"}


# ---------- small, single-purpose helpers (easy to test) ----------

def slugify(s) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-")
    return s or "unknown"


def split_list(cell) -> list[str]:
    """'yuzu, Citruses' -> ['yuzu', 'citruses']; drops noise; keeps order; de-dupes."""
    if pd.isna(cell):
        return []
    out = []
    for tok in str(cell).split(","):
        t = tok.strip().lower()
        if t and t not in NOISE:
            out.append(t)
    return list(dict.fromkeys(out))  # order-preserving de-dup


def eu_float(cell):
    """European decimal string -> float. '1,42' -> 1.42"""
    if pd.isna(cell):
        return None
    try:
        return float(str(cell).replace(",", ".").strip())
    except ValueError:
        return None


def to_int(cell):
    if pd.isna(cell):
        return None
    digits = re.sub(r"[^\d]", "", str(cell))
    return int(digits) if digits else None


def frag_id(url) -> str | None:
    """Extract Fragrantica's numeric id from the URL: .../accento-...-74630.html -> '74630'."""
    m = re.search(r"-(\d+)\.html", str(url))
    return m.group(1) if m else None


def to_year(cell):
    """'2022.0' -> 2022; guards obviously-bad values."""
    if pd.isna(cell):
        return None
    try:
        y = int(float(str(cell).replace(",", ".")))
        return y if 1800 <= y <= 2100 else None
    except ValueError:
        return None


def prettify(slug) -> str:
    """'accento-overdose-pride-edition' -> 'Accento Overdose Pride Edition'."""
    return re.sub(r"[-_]+", " ", str(slug)).strip().title()


# ---------- the loader ----------

def load() -> pd.DataFrame:
    if not RAW.exists():
        raise FileNotFoundError(f"Missing {RAW}. Run scripts/download_data.py first.")

    df = pd.read_csv(RAW, sep=";", encoding="latin-1", engine="python", on_bad_lines="skip")
    print(f"raw rows read:        {len(df):,}")

    df = df.drop_duplicates(subset=["url"]).reset_index(drop=True)
    print(f"after URL de-dupe:    {len(df):,}")

    records, bad = [], 0
    for _, r in df.iterrows():
        top = split_list(r.get("Top"))
        mid = split_list(r.get("Middle"))
        base = split_list(r.get("Base"))

        accords = []
        for c in ACCORD_COLS:
            accords += split_list(r.get(c))
        accords = list(dict.fromkeys(accords))

        perfumers = []
        for c in ("Perfumer1", "Perfumer2"):
            perfumers += split_list(r.get(c))

        fid = frag_id(r.get("url"))
        pid = f"{slugify(r.get('Brand'))}__{fid}" if fid else \
              f"{slugify(r.get('Brand'))}-{slugify(r.get('Perfume'))}"

        try:
            p = Perfume(
                id=pid,
                name=prettify(r.get("Perfume")),
                brand=prettify(r.get("Brand")),
                year=to_year(r.get("Year")),
                gender=(None if pd.isna(r.get("Gender")) else str(r.get("Gender")).strip().lower()),
                country=(None if pd.isna(r.get("Country")) else str(r.get("Country")).strip()),
                rating=eu_float(r.get("Rating Value")),
                rating_count=to_int(r.get("Rating Count")),
                accords=accords,
                notes_top=top,
                notes_middle=mid,
                notes_base=base,
                notes_all=list(dict.fromkeys(top + mid + base)),
                perfumers=perfumers,
                url=str(r.get("url")).strip(),
            )
            records.append(p.model_dump())
        except Exception as e:       # a row that fails the schema is reported, not fatal
            bad += 1
            if bad <= 5:
                print("  skipped (schema):", e)

    out = pd.DataFrame.from_records(records)

    # quality gate: a perfume with zero notes can't be recommended on notes
    before = len(out)
    out = out[out["notes_all"].map(len) > 0].reset_index(drop=True)
    print(f"validated rows:       {len(records):,}  (schema-bad: {bad})")
    print(f"dropped (no notes):   {before - len(out):,}")

    # nullable integer dtype so year/count stay ints even with missing values
    for col in ("year", "rating_count"):
        out[col] = out[col].astype("Int64")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT, index=False)
    print(f"\nwrote {len(out):,} perfumes -> {OUT}")
    return out


if __name__ == "__main__":
    df = load()
    print("\n--- sample record ---")
    print(json.dumps(df.iloc[0].to_dict(), indent=2, default=str))
    print("\n--- sanity checks ---")
    print("null ratings:", df["rating"].isna().sum())
    print("rows w/ full pyramid:",
          int(df[["notes_top", "notes_middle", "notes_base"]].apply(
              lambda r: all(len(x) > 0 for x in r), axis=1).sum()))
    print("distinct brands:", df["brand"].nunique())
