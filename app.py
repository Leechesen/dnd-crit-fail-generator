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

st.set_page_config(
    page_title="D&D Crit Fail Generator",
    layout="centered"
)

st.title("🎲 D&D Crit Fail Generator")
st.caption("Offline • D&D 2024 compatible • DM tool")

# ==================================================
# SESSION STATE
# ==================================================

if "log" not in st.session_state:
    st.session_state.log = []

# ==================================================
# UI – STEP 1: TYPE OF ACTION
# ==================================================

action_type = st.selectbox(
    "Typ akce:",
    ["Útok"]
)

# ==================================================
# UI – STEP 2: ATTACK TYPE (ONLY IF ATTACK)
# ==================================================

attack_type = None

if action_type == "Útok":
    attack_type = st.radio(
        "Typ útoku:",
        ["melee", "ranged"],
        horizontal=True
    )

# ==================================================
# UI – STEP 3: SEVERITY
# ==================================================

severity = st.selectbox(
    "Závažnost:",
    ["light", "medium", "heavy"]
)

# ==================================================
# RANDOM SELECTION (WEIGHTED)
# ==================================================

def get_random_crit_fail(data):
    weights = [item.get("weight", 1) for item in data]
    return random.choices(data, weights=weights, k=1)[0]

# ==================================================
# BUTTON
# ==================================================

if st.button("🎲 CRIT FAIL"):
    if not attack_type:
        st.warning("Vyber typ útoku.")
    else:
        pool = CRIT_FAILS[attack_type][severity]

        if not pool:
            st.warning("Pro tuto kombinaci zatím nejsou žádná data.")
        else:
            result = get_random_crit_fail(pool)

            # Save to log
            st.session_state.log.insert(0, {
                "action": action_type,
                "attack_type": attack_type,
                "severity": severity,
                "effect": result["effect"],
                "roleplay": result["roleplay"]
            })

            # Keep last 5
            st.session_state.log = st.session_state.log[:5]

            # Display result
            st.markdown("## 📜 Výsledek")

            st.markdown(f"**Herní efekt:**  \n{result['effect']}")
            st.markdown("")
            st.markdown("**Popis (roleplay):**")
            st.markdown(f"- {result['roleplay'][0]}")
            st.markdown(f"- {result['roleplay'][1]}")

# ==================================================
# LOG
# ==================================================

if st.session_state.log:
    st.markdown("---")
    st.markdown("## 🧾 Poslední crit faily")

    for i, entry in enumerate(st.session_state.log):
        with st.expander(
            f"{i+1}. {entry['action']} | {entry['attack_type']} | {entry['severity']}"
        ):
            st.markdown(f"**Herní efekt:**  \n{entry['effect']}")
            st.markdown("")
            st.markdown("**Popis (roleplay):**")
            st.markdown(f"- {entry['roleplay'][0]}")
            st.markdown(f"- {entry['roleplay'][1]}")
