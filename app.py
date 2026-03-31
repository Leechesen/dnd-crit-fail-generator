import streamlit as st
import json
import random
import os
from excel_to_json import build_json_from_excel

st.set_page_config(layout="wide")

EXCEL_FILE = "crit_fails.xlsx"
OUTPUT_JSON = "crit_fails.json"

# =========================
# AUTO UPDATE
# =========================

if not os.path.exists(OUTPUT_JSON):
    build_json_from_excel()
elif os.path.getmtime(EXCEL_FILE) >= os.path.getmtime(OUTPUT_JSON):
    build_json_from_excel()

# =========================
# LOAD
# =========================

with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)

# =========================
# SESSION
# =========================

if "result" not in st.session_state:
    st.session_state.result = None

if "severity" not in st.session_state:
    st.session_state.severity = "Lehký"

# =========================
# CSS (AUTO WIDTH BUTTONS)
# =========================

st.markdown("""
<style>

/* tlačítka podle textu */
div.stButton > button {
    height: 60px;
    font-size: 18px;
    font-weight: 600;
    padding: 0 20px;

    width: auto !important;
    min-width: 120px;

    white-space: nowrap;
}

/* zarovnání vedle sebe */
.stButton {
    display: inline-block;
    margin: 5px;
}

</style>
""", unsafe_allow_html=True)

# =========================
# GENERATE
# =========================

def weighted_choice(pool):
    total = sum(item.get("weight", 1) for item in pool)
    r = random.uniform(0, total)
    upto = 0
    for item in pool:
        w = item.get("weight", 1)
        if upto + w >= r:
            return item
        upto += w
    return random.choice(pool)


def generate(pool):
    if not pool:
        st.session_state.result = {"effect": "❌ Žádná data", "roleplay": []}
    else:
        st.session_state.result = weighted_choice(pool)

    st.rerun()

# =========================
# UI
# =========================

st.title("🎲 DnD Crit Fail")

# RESULT
if st.session_state.result:
    r = st.session_state.result
    st.subheader("💥 Efekt")
    st.write(r.get("effect", ""))

    st.subheader("🎭 Roleplay")
    for rp in r.get("roleplay", []):
        if rp:
            st.write("•", rp)

st.markdown("---")

# =========================
# SEVERITY
# =========================

col1, col2, col3, col4 = st.columns(4)

if col1.button("🟢 Lehký"):
    st.session_state.severity = "Lehký"
if col2.button("🟠 Střední"):
    st.session_state.severity = "Střední"
if col3.button("🔴 Těžký"):
    st.session_state.severity = "Těžký"
if col4.button("🟣 Sranda"):
    st.session_state.severity = "Sranda"

st.write("Závažnost:", st.session_state.severity)

st.markdown("---")

colA, colB, colC = st.columns(3)

# =========================
# ⚔️ ÚTOK
# =========================

with colA:
    st.subheader("⚔️ Útok")

    attack_data = data.get("Útok", {})

    for attack_type, severity_dict in attack_data.items():
        if st.button(
            attack_type,
            key=f"attack_{attack_type}"
        ):
            pool = severity_dict.get(st.session_state.severity)

            if not pool:
                pool = next(iter(severity_dict.values()), [])

            generate(pool)

# =========================
# 🛡️ OBRANA
# =========================

with colB:
    st.subheader("🛡️ Obrana")

    defense_data = data.get("Obrana", {})

    if st.button("🛡️ Obrana", key="defense_btn"):
        pool = defense_data.get(st.session_state.severity)

        if not pool:
            pool = next(iter(defense_data.values()), [])

        generate(pool)

# =========================
# 🎲 SKILLY (AUTO WIDTH)
# =========================

with colC:
    st.subheader("🎲 Skilly")

    for attr, skills in data.get("Skill", {}).items():

        st.markdown(f"### {attr}")

        for skill_name, skill_data in skills.items():

            pool = skill_data.get(st.session_state.severity)

            if not pool:
                pool = next(iter(skill_data.values()), [])

            if st.button(
                skill_name,
                key=f"{attr}_{skill_name}"
            ):
                generate(pool)
