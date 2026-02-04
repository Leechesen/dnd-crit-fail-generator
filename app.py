import streamlit as st
import json
import random

# ==================================================
# LOAD DATA
# ==================================================

with open("crit_fails.json", "r", encoding="utf-8") as f:
    DATA = json.load(f)

# ==================================================
# STREAMLIT CONFIG
# ==================================================

st.set_page_config(
    page_title="D&D Crit Fail Generator",
    layout="centered"
)

st.title("🎲 D&D Crit Fail Generator")
st.caption("JSON-driven • D&D 2024 • DM tool")

# ==================================================
# SESSION STATE
# ==================================================

if "log" not in st.session_state:
    st.session_state.log = []

# ==================================================
# UI – STEP 1: ACTION TYPE
# ==================================================

action_type = st.selectbox(
    "Typ akce:",
    list(DATA.keys())  # Útok, Obrana, Kouzlo, Skill
)

# ==================================================
# UI – STEP 2: ATTACK TYPE (ONLY FOR ÚTOK)
# ==================================================

attack_type = None
severity = None

if action_type == "Útok":
    attack_type = st.radio(
        "Typ útoku:",
        list(DATA["Útok"].keys()),  # Melee / Ranged
        horizontal=True
    )

    severity = st.selectbox(
        "Závažnost:",
        list(DATA["Útok"][attack_type].keys())  # Lehký / Střední / Těžký
    )
else:
    severity = st.selectbox(
        "Závažnost:",
        list(DATA[action_type].keys())
    )

# ==================================================
# RANDOM PICK (WEIGHTED)
# ==================================================

def pick_random(pool):
    weights = [item.get("weight", 1) for item in pool]
    return random.choices(pool, weights=weights, k=1)[0]

# ==================================================
# BUTTON
# ==================================================

if st.button("🎲 CRIT FAIL"):
    if action_type == "Útok":
        pool = DATA["Útok"][attack_type][severity]
    else:
        pool = DATA[action_type][severity]

    if not pool:
        st.warning("Pro tuto kombinaci zatím nejsou žádná data.")
    else:
        result = pick_random(pool)

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

        # ==============================
        # DISPLAY RESULT
        # ==============================

        st.markdown("## 📜 Výsledek")

        if attack_type:
            st.markdown(f"**Akce:** {action_type} ({attack_type})")
        else:
            st.markdown(f"**Akce:** {action_type}")

        st.markdown(f"**Závažnost:** {severity}")
        st.markdown("")
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
        label = entry["action"]
        if entry["attack_type"]:
            label += f" ({entry['attack_type']})"

        with st.expander(f"{i+1}. {label} | {entry['severity']}"):
            st.markdown(f"**Herní efekt:**  \n{entry['effect']}")
            st.markdown("")
            st.markdown("**Popis (roleplay):**")
            st.markdown(f"- {entry['roleplay'][0]}")
            st.markdown(f"- {entry['roleplay'][1]}")
