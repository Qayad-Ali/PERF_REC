
"""
Lightweight agent: LLM PLANS (mode, query, city, filters) -> executor RUNS tools
(get_climate, search, suggest_layers) and SELF-CORRECTS (retries looser if thin)
-> LLM COMPOSES a grounded answer. Manual JSON routing (works with local gemma).

"""
from __future__ import annotations
import sys, json
from pathlib import Path
from openai import OpenAI

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from perfrec.retrieve.search import search
from perfrec.layering.layer import suggest_layers, application_tip

MODEL = "gemma4:e4b-it-qat"
llm = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

# --- TOOL: city -> climate hint (stand-in for a weather API) ---
CITY_CLIMATE = {"delhi":0.7,"mumbai":0.7,"chennai":0.7,"dubai":0.7,"singapore":0.7,
                "bangkok":0.7,"london":0.2,"paris":0.2,"moscow":0.1,"toronto":0.2,"berlin":0.2}
def get_climate(city):
    return CITY_CLIMATE.get(city.strip().lower()) if city else None

def _json(raw):
    s, e = raw.find("{"), raw.rfind("}")
    return json.loads(raw[s:e+1])

# --- 1. PLAN ---
def plan(request):
    sys_p = (
        'You plan a perfume assistant. Output ONLY JSON: '
        '{"mode":"single"|"layering"|"both","semantic_query":"...","city":"city or null",'
        '"min_longevity":0-1 or null,"gender":"men|women|unisex|null"}. '
        'Use "layering" if they mention layering/combining/mixing; "both" if they want depth but are vague.'
    )
    r = llm.chat.completions.create(model=MODEL, temperature=0,
        messages=[{"role":"system","content":sys_p},{"role":"user","content":request}])
    return _json(r.choices[0].message.content)

# --- 2. ACT (with self-correction) ---
def act(p):
    min_climate = get_climate(p.get("city"))          # tool call
    out = {"min_climate": min_climate, "singles": [], "pairs": []}
    q = p.get("semantic_query") or ""

    if p.get("mode") in ("single", "both"):
        hits = search(q, min_climate=min_climate, min_longevity=p.get("min_longevity"),
                      gender=p.get("gender"), limit=6)
        if len(hits) < 3 and min_climate:             # SELF-CORRECT
            print("  [agent] thin results — loosening climate filter and retrying")
            hits = search(q, min_climate=max(0.0, min_climate - 0.3),
                          min_longevity=p.get("min_longevity"), gender=p.get("gender"), limit=6)
        out["singles"] = hits

    if p.get("mode") in ("layering", "both"):
        out["pairs"] = suggest_layers(q, top=3)
    for _, anc, lif, parts in out["pairs"]:
        print(f"  [pair] {lif.payload['name']} + {anc.payload['name']} {parts}")    
    return out

# --- 3. COMPOSE (grounded) ---
def compose(request, results):
    singles = "\n".join(
        f"- {h.payload['name']} by {h.payload['brand']} | {h.payload['family']} | "
        f"accords: {', '.join(h.payload['accords'][:6])} | notes: {', '.join(h.payload['notes_all'][:8])}"
        for h in results["singles"])
    pairs = "\n".join(f"- {lif.payload['name']} + {anc.payload['name']}"
                      for _, anc, lif, _ in results["pairs"])
    ctx = f"SINGLES:\n{singles or '(none)'}\n\nLAYERS:\n{pairs or '(none)'}"
    sys_p = ("You are a perfume advisor. Recommend ONLY from the candidates below — never invent "
             "perfumes or notes. Explain why picks fit the request and climate. If layers are given, "
             "recommend the best one and how to apply it.")
    r = llm.chat.completions.create(model=MODEL, temperature=0.4,
        messages=[{"role":"system","content":sys_p},
                  {"role":"user","content":f"Request: {request}\n\n{ctx}"}])
    return r.choices[0].message.content.strip()

def run(request):
    p = plan(request); print("plan:", p, "\n")
    results = act(p)
    print("\n--- answer ---\n")
    print(compose(request, results))

if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "I'm in Delhi, humid, want a fresh office scent I can also layer"
    run(q)
