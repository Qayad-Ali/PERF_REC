##this step is enrichment of data ,family,longevity,projection,climate_hot_humid

from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[3]

IN = ROOT / "data" / "processed" / "perfumes_sunnah.parquet"
OUT=ROOT/"data"/"processed"/"perfumes_enriched.parquet"

FAMILY={"citrus":"Fresh","aquatic":"Fresh","green":"Fresh","fresh":"Fresh",
    "fresh spicy":"Fresh","ozonic":"Fresh","marine":"Fresh","aromatic":"Fresh",
    "woody":"Woody","mossy":"Woody","earthy":"Woody","chypre":"Woody",
    "leather":"Woody","leathery":"Woody",
    "amber":"Amber","warm spicy":"Amber","sweet":"Amber","vanilla":"Amber",
    "gourmand":"Amber","balsamic":"Amber","oud":"Amber","tobacco":"Amber","powdery":"Amber",
    "floral":"Floral","white floral":"Floral","rose":"Floral","yellow floral":"Floral",
    "tuberose":"Floral","violet":"Floral","iris":"Floral","fruity":"Floral",
    "tropical":"Floral","soft spicy":"Floral","musky":"Floral","animalic": "Amber", "balsamic": "Amber", "honey": "Amber", "oud": "Amber",
   "smoky": "Woody", "conifer": "Woody",
   "aldehydic": "Floral", "soft spicy": "Floral",
   "metallic": "Fresh",}

HEAVY={"oud","amber","musk","vanilla","patchouli","sandalwood","tonka","benzoin",
         "labdanum","incense","leather","oakmoss","myrrh","cedar","vetiver"}

LOUD = {"sweet","amber","warm spicy","oud","gourmand","tobacco","vanilla","balsamic"}
SOFT = {"musky","powdery","woody","mossy","earthy","aromatic"}
# hot-humid suitability
HOT_GOOD = {"citrus","aquatic","green","fresh","ozonic","marine","fresh spicy","aromatic","fruity"}
HOT_BAD  = {"sweet","amber","gourmand","vanilla","warm spicy","oud","tobacco","balsamic"}

def as_list(x):
    return [] if x is None else list(x)

def clamp(x):return max(0.0,min(1.0,x))

def family_of(accords):
    for a in as_list(accords):
        if a in FAMILY:
            return FAMILY[a]

    return "unclassified"

def longevity_of(row):
    base=as_list(row["notes_base"])
    heavy_hits=sum(1 for n in base if any(h in n for h in HEAVY))
    return round(clamp(0.15*len(base)+0.20*heavy_hits),3)


def projection_of(accords):
    acc=as_list(accords)
    loud=sum(1 for a in acc if a in LOUD)
    soft=sum(1 for a in acc if a in SOFT)
    return round(clamp(0.5 +0.18*loud-0.12*soft),3)

def hit_humid_fit(accords):
    acc=as_list(accords)
    good=sum(1 for a in acc if a in HOT_GOOD)
    bad=sum(1 for a in acc if a in HOT_BAD)
    return round(clamp(0.5+0.2*good-0.2*bad),3)

def hot_humid_fit(accords):
    acc=as_list(accords)
    good=sum(1 for a in acc if a in HOT_GOOD)
    bad=sum(1 for a in acc if a in HOT_BAD)
    return round(clamp(0.5+0.2*good-0.2*bad),3)

def enrich():
    df = pd.read_parquet(IN)
    df["family"]            = df["accords"].map(family_of)
    df["longevity"]         = df.apply(longevity_of, axis=1)
    df["projection"]        = df["accords"].map(projection_of)
    df["climate_hot_humid"] = df["accords"].map(hot_humid_fit)

    df.to_parquet(OUT, index=False)
    print(f"wrote {len(df):,} -> {OUT}\n")
    print(df["family"].value_counts(), "\n")
    print(df[["name","family","longevity","projection","climate_hot_humid"]].head(8).to_string())
    return df

if __name__=="__main__":
    enrich()
