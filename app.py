import streamlit as st
import json
import random

# ==================================================
# LOAD DATA
# ==================================================

with open("crit_fails.json", "r", encoding="utf-8") as f:
    CRIT_FAILS = json.load(f)

# ==================================================
# STREAMLIT CONFIG
# ==================================================

st.set_page_config(page_title="D&D Crit Fail Generator", layout="centered")
st.title("🎲 D&D Crit Fail Generator (Offline)")

# ==================================================
# SESSION LOG
# ==================================================

if "log" not in st.session_state:
    st.session_state.log = []

# ==================================================
# UI
# ==================================================

typ_akce = st.selectbox(
    "Typ akce:",
    list(CRIT_FAILS.keys())
)

zavaznost = st.selectbox(
    "Závažnost:",
    list(CRIT_FAILS[typ_akce].keys())
)

# ==================================================
# RANDOM VÝBĚR S VÁHAMI
# ==================================================

def nahodny_crit_fail(typ, zavaznost):
    moznosti = CRIT_FAILS[typ][zavaznost]
    vahy = [m.get("weight", 1) for m in moznosti]
    return random.choices(moznosti, weights=vahy, k=1)[0]

# ==================================================
# BUTTON
# ==================================================

if st.button("🎲 CRIT FAIL"):
    vysledek = nahodny_crit_fail(typ_akce, zavaznost)

    st.session_state.log.insert(0, {
        "typ": typ_akce,
        "zavaznost": zavaznost,
        "popis": vysledek["effect"],
        "efekt": vysledek["roleplay"]
    })

    st.session_state.log = st.session_state.log[:5]

    st.markdown("### 📜 Výsledek")
    st.markdown(f"""
**Popis:**  
{vysledek["popis"]}

**Herní efekt:**  
{vysledek["efekt"]}
""")

# ==================================================
# LOG
# ==================================================

if st.session_state.log:
    st.markdown("---")
    st.markdown("### 🧾 Poslední crit faily")

    for i, z in enumerate(st.session_state.log):
        with st.expander(f"{i+1}. {z['typ']} | {z['zavaznost']}"):
            st.markdown(f"""
**Popis:**  
{z["popis"]}

**Herní efekt:**  
{z["efekt"]}
""")

