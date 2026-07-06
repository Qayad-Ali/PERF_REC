import sys
from pathlib import Path
import streamlit as st
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from perfrec.generate.recommend import understand, generate
from perfrec.retrieve.search import search
from perfrec.layering.layer import suggest_layers, application_tip

st.set_page_config(page_title="PerfRec",page_icon="🌿",layout="centered")
st.title("🌿 PerfRec")
st.caption("Climate-aware,layering-first perfume recommendations RAG over 21k fragrances")

query=st.text_input("Describe your situation","I live in Delhi ,its hot and humid,office wear,want compliments")

if st.button("Recommend", type="primary") and query:
    with st.spinner("Understanding your request…"):
        intent = understand(query)
        if intent.get("min_climate"):
            intent["min_climate"] = min(intent["min_climate"], 0.7)   # don't over-filter
    st.write("**Understood as:**", intent)

    with st.spinner("Finding perfumes…"):
        hits = search(intent.get("semantic_query") or query,
                      min_climate=intent.get("min_climate"),
                      min_longevity=intent.get("min_longevity"),
                      gender=intent.get("gender"), limit=6)
    with st.spinner("Writing recommendation (local LLM)…"):
        answer = generate(query, hits)

    st.subheader("Recommended for you")
    st.write(answer)

    with st.expander("See the retrieved candidates"):
        for h in hits:
            p = h.payload
            st.markdown(f"**{p['name']}** — {p['brand']} · {p['family']} · "
                        f"climate {p['climate_hot_humid']} · longevity {p['longevity']}")

    st.subheader("💧 Try layering")
    with st.spinner("Building layering pairs…"):
        pairs = suggest_layers(intent.get("semantic_query") or query, top=3)
    for score, anc, lif, parts in pairs:
        st.markdown(f"**{lif.payload['name']}  +  {anc.payload['name']}** · score {score}")
        st.caption(application_tip(anc, lif))
