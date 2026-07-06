

from pathlib import Path
import urllib.request
from dotenv import load_dotenv

load_dotenv()
RAW = Path("data/raw")

PARFUMO_CSV = (
    "https://raw.githubusercontent.com/rfordatascience/tidytuesday/"
    "main/data/2024/2024-12-10/parfumo_data_clean.csv"
)


def download_url(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"↓ {url}\n  -> {dest}")
    urllib.request.urlretrieve(url, dest)
    print(f"  done ({dest.stat().st_size / 1e6:.1f} MB)")


def download_kaggle(dataset: str, subdir: str) -> None:
    """Best-effort Kaggle download. Never fatal."""
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        api = KaggleApi()
        api.authenticate()
        dest = RAW / subdir
        dest.mkdir(parents=True, exist_ok=True)
        print(f"↓ Kaggle: {dataset} -> {dest}")
        api.dataset_download_files(dataset, path=str(dest), unzip=True)
        print("  done")
    except Exception as e:
        print(f"  [skipped] Kaggle step failed ({type(e).__name__}): {e}")
        print("  Parfumo CSV is enough to start. Sort out Fragrantica reviews later.")


if __name__ == "__main__":
    # 1) Parfumo — reliable primary base table
    download_url(PARFUMO_CSV, RAW / "parfumo" / "parfumo_data_clean.csv")

    # 2) Fragrantica reviews — optional enrichment (needs Kaggle access)
    download_kaggle("olgagmiufana1/fragrantica-com-fragrance-dataset", "fragrantica")

    print("\nDone. Raw data in data/raw/  (gitignored). Next: notebooks/01_profile.ipynb")
