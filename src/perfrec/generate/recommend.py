##Query understanding + grounded generation, via local Ollama (gemma4
##Flow:  user sentence -> LLM extracts filters -> filtered vector search
 ##      -> LLM writes a recommendation grounded ONLY in the retrieved perfumes.


from __future__ import annotations

import sys,json
from pathlib import Path
from openai import OpenAI

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from perfrec.retrieve.search import search
MODEL = "gemma4:e4b-it-qat"
llm=OpenAI(base_url="http://localhost:11434/v1",api_key="ollama")

def _json_from(raw:str)->dict:
    s,e=raw.find("{"),raw.rfind("}")
    return json.loads(raw[s:e+1])

def understand(text:str)->dict:
    system=(
        "Convert a perfume request into JSON filters. Return ONLY a JSON object with keys: "
        "semantic_query (string: a concise scent description to search for), "
        "min_climate (float 0-1 or null: high when the user is in hot/humid weather), "
        "min_longevity (float 0-1 or null: high when they want it to last), "
        "gender ('men'|'women'|'unisex'|null). No prose."
    )
    r=llm.chat.completions.create(model=MODEL,temperature=0,messages=[{"role": "system", "content": system},
                  {"role": "user", "content": text}],
    )
    return _json_from(r.choices[0].message.content)

def generate(text:str,hits)->str:
    lines=[]
    for h in hits:
        p=h.payload
        lines.append( f"- {p['name']} by {p['brand']} | family: {p['family']} | "
            f"accords: {', '.join(p['accords'][:6])} | longevity: {p['longevity']} | "
            f"climate_fit: {p['climate_hot_humid']} | notes: {', '.join(p['notes_all'][:10])}"
        )
    context="\n".join(lines)
    system=   (
        "You are a perfume  expert and advisor. Recommend ONLY from the candidates provided — "
        "never invent a perfume or a note. In 2-4 short paragraphs, pick the best few and "
        "explain WHY each fits the user's climate and request, citing their accords/notes."
    )  

    user=f"User request:{text}\n\nCandidates:\m{context}"
    r=llm.chat.completions.create(model=MODEL,temperature=0.4,messages=[{"role":"system","content":system},{"role":"user","content":user}],)
    return r.choices[0].message.content.strip()



def recommend(text:str,k:int=6)->str:
    intent = understand(text)
    if intent.get("min_climate"): intent["min_climate"] = min(intent["min_climate"], 0.7)
    print("parsed intent:",intent,"\n")
    hits=search(intent.get("semantic_query") or text,min_climate=intent.get("min_climate"),min_longevity=intent.get("min_longevity"),gender=intent.get("gender"),limit=k,)
    print("\n recommendation  \n")
    answer=generate(text,hits)
    print(answer)
    return answer


if __name__=="__main__":
    q=sys.argv[1] if len(sys.argv)>1 else \
        "I live in Delhi, it's hot and humid, office wear, want compliments"
    recommend(q)
                                                                         
 
