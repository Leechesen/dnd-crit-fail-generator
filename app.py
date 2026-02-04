import streamlit as st
import json
import random

# =========================
# LOAD DATA
# =========================

with open("crit_fails.json", "r", encoding="utf-8") as f:
    DATA = json.load(f)

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(
    page_title="D&D Crit Fail Generator",
    page_icon="🎲",
    layout="centered"
)

st.title("🎲 D&D Crit Fail Generator")
st.caption("Excel → JSON → Streamlit | D&D 2024")

# =========================
# HELPERS
# =========================

def weighted_random(items):
    weights = [item.get("weight", 1) for item in items]
    return random.choices(items, weights=weights, k=1)[0]

# =========================
# UI – ACTION TYPE
# =========================

action_type = st.selectbox(
    "Typ akce",
    list(DATA.keys())
)

# =========================
# UI – ATTACK TYPE (ONLY FOR ÚTOK)
# =========================

attack_type = None

if action_type == "Útok":
    attack_type = st.radio(
        "Typ útoku",
        list(DATA["Útok"].keys()),
        horizontal=True
    )

    severities = list(DATA["Útok"][attack_type].keys())
else:
    severities = list(DATA[action_type].keys())

# =========================
# UI – SEVERITY
# =========================

severity = st.selectbox(
    "Závažnost",
    severities
)

# =========================
# BUTTON
# =========================

if st.button("🎲 Generuj Crit Fail"):
    if action_type == "Útok":
        pool = DATA["Útok"][attack_type].get(severity, [])
    else:
        pool = DATA[action_type].get(severity, [])

    if not pool:
        st.warning("Pro tuto kombinaci nejsou žádná data.")
    else:
        result = weighted_random(pool)

        # =========================
        # OUTPUT
        # =========================

        st.markdown("---")
        st.markdown("## 📜 Výsledek")

        if attack_type:
            st.markdown(f"**Akce:** {action_type} ({attack_type})")
        else:
            st.markdown(f"**Akce:** {action_type}")

        st.markdown(f"**Závažnost:** {severity}")
        st.markdown("")

        st.markdown("### 🎯 Herní efekt")
        st.markdown(result["effect"])

        st.markdown("")
        st.markdown("### 🎭 Popis (DM → hráč)")
        st.markdown(f"- {result['roleplay'][0]}")
        st.markdown(f"- {result['roleplay'][1]}")

# =========================
# FOOTER
# =========================

st.markdown("---")
st.caption("Data se načítají automaticky z Excelu přes GitHub Actions.")
