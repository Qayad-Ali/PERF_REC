"""
The canonical Perfume record — the CONTRACT for the whole pipeline.

Everything downstream (enrichment, embedding, retrieval, generation) reads this
shape, never the raw CSV. Keeping one clean, typed schema is what stops messy
source data from leaking into your engine.

MVP scope: this holds the cleaned raw fields only. Step 2 (enrichment) will add
derived fields (family, volatility, longevity, projection, climate_fit) — either
by extending this model or via a separate EnrichedPerfume model.
"""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class Perfume(BaseModel):
    id: str                      # stable unique id, e.g. "xerjoff__74630"
    name: str
    brand: str
    year: Optional[int] = None
    gender: Optional[str] = None      # "men" | "women" | "unisex"
    country: Optional[str] = None

    rating: Optional[float] = None    # 0–5 scale (Fragrantica); keep the scale in mind
    rating_count: Optional[int] = None

    accords: List[str] = Field(default_factory=list)        # community-voted accords
    notes_top: List[str] = Field(default_factory=list)
    notes_middle: List[str] = Field(default_factory=list)
    notes_base: List[str] = Field(default_factory=list)
    notes_all: List[str] = Field(default_factory=list)      # union, handy for search/embedding

    perfumers: List[str] = Field(default_factory=list)
    url: str
    source: str = "fragrantica_fra_cleaned"
