from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
IN  = ROOT / "data" / "processed" / "perfumes_enriched.parquet"
OUT = ROOT / "data" / "processed" / "perfumes_docs.parquet"


def as_list(x):
    return [] if x is None else list(x)

def perf_words(longevity,projection):
    lon=("very long lasting" if longevity>0.8 else
         "long lasting" if longevity>0.6 else
         "moderate longevity" if longevity>0.35 else
         "weak longevity")
    
    pro=("heavy projection" if projection>=0.7 else
         "moderate projection" if projection>=0.45 else "soft projection")
    return lon,pro

def build_document(row):
    desc = (row["description"] or "").strip()
    lon, pro = perf_words(row["longevity"], row["projection"])
    accords = ", ".join(as_list(row["accords"]))
    extra = f" Family: {row['family']}. Main accords: {accords}. Performance: {lon}, {pro}."
    if desc:
        return desc + extra          # real description + structured signals it may omit
    # fallback: synthesize (your old logic) when a description is missing
    top = ", ".join(as_list(row["notes_top"]))
    return f"{row['name']} by {row['brand']}. A {row['family'].lower()} fragrance. " \
           f"Top: {top}.{extra}"

def build():
    df=pd.read_parquet(IN)
    df["document"]=df.apply(build_document,axis=1)
    df.to_parquet(OUT,index=False)
    print(F"wrote {len(df):,}->{OUT}\n"
          )
    print("example document:\n", df["document"].iloc[0], "\n")
    print("doc length (chars):\n", df["document"].str.len().describe().round(0).to_string())
    return df

if __name__=="__main__":
    build()
                                
