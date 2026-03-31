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
# CSS
# =========================

st.markdown("""
<style>
div.stButton > button {
    height: 80px;
    font-size: 20px;
    font-weight: 700;
    white-space: nowrap;
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
    cols = st.columns(len(attack_data))

    for i, (attack_type, severity_dict) in enumerate(attack_data.items()):

        if cols[i].button(
            attack_type,
            key=f"attack_{attack_type}",
            use_container_width=True
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

    if st.button(
        "🛡️ Obrana",
        key="defense_btn",
        use_container_width=True
    ):
        pool = defense_data.get(st.session_state.severity)

        if not pool:
            pool = next(iter(defense_data.values()), [])

        generate(pool)

# =========================
# 🎲 SKILLY
# =========================

with colC:
    st.subheader("🎲 Skilly")

    max_cols = 2

    for attr, skills in data.get("Skill", {}).items():

        st.markdown(f"### {attr}")

        skill_items = list(skills.items())

        for j in range(0, len(skill_items), max_cols):
            row = skill_items[j:j+max_cols]
            cols = st.columns(len(row))

            for i, (skill_name, skill_data) in enumerate(row):

                pool = skill_data.get(st.session_state.severity)

                if not pool:
                    pool = next(iter(skill_data.values()), [])

                if cols[i].button(
                    skill_name,
                    key=f"{attr}_{skill_name}",
                    use_container_width=True
                ):
                    generate(pool)
