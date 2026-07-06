# src/perfrec/ingest/load_sunnahscents.py
"""
Loader for the scraped fragrances.csv (SunnahScents schema) -> canonical parquet.
Handles: stringified note lists, accords as [{'name','strength'}] with messy quoting,
and keeps the rich `description` (great for embeddings).
Run:  python src/perfrec/ingest/load_sunnahscents.py
"""
from __future__ import annotations
import ast, re, sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
ROOT = Path(__file__).resolve().parents[3]
RAW  = ROOT / "data" / "fragrances.csv"
OUT  = ROOT / "data" / "processed" / "perfumes_sunnah.parquet"

NOISE = {"", "unknown", "n/a", "none"}


def slug(s): return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-") or "x"

def parse_notes(cell):
    if pd.isna(cell): return []
    try:
        return [str(x).strip().lower() for x in ast.literal_eval(cell) if str(x).strip()]
    except Exception:
        return []

def parse_accords(cell):
    """Tolerant parse of [{'name': '...', 'strength': N}] even with mangled quotes."""
    if pd.isna(cell): return []
    out = []
    for name, strength in re.findall(r"'name':\s*(.*?),\s*'strength':\s*(\d+)", str(cell)):
        n = re.sub(r"[\\'\"]", "", name).strip().lower()   # strip stray \ ' " from the name
        if n and n not in NOISE:
            out.append((n, int(strength)))
    out.sort(key=lambda x: -x[1])                          # strongest accord first
    return [n for n, _ in out]

def num(x, cast):
    if pd.isna(x): return None
    try: return cast(float(str(x)))
    except ValueError: return None


def load():
    df = pd.read_csv(RAW, engine="python", on_bad_lines="skip")
    print(f"raw rows: {len(df):,}")

    recs = []
    for _, r in df.iterrows():
        top  = parse_notes(r.get("top_notes"))
        mid  = parse_notes(r.get("middle_notes"))
        base = parse_notes(r.get("base_notes"))
        recs.append({
            "id": f"{slug(r.get('brand'))}__{slug(r.get('name'))}",
            "name": str(r.get("name")).strip(),
            "brand": str(r.get("brand")).strip(),
            "gender": (str(r.get("gender")).strip().lower() if not pd.isna(r.get("gender")) else None),
            "rating": num(r.get("review_average"), float),
            "rating_count": num(r.get("review_count"), int),
            "accords": parse_accords(r.get("accords")),
            "notes_top": top, "notes_middle": mid, "notes_base": base,
            "notes_all": list(dict.fromkeys(top + mid + base)),
            "description": (str(r.get("description")).strip() if not pd.isna(r.get("description")) else ""),
            "source": "sunnahscents",
        })

    out = pd.DataFrame(recs)
    out = out.drop_duplicates(subset="id").reset_index(drop=True)
    out = out[out["notes_all"].map(len) > 0].reset_index(drop=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT, index=False)
    print(f"wrote {len(out):,} -> {OUT}")
    print(out[["name","brand","gender","accords"]].head(3).to_string())
    return out


if __name__ == "__main__":
    load()
