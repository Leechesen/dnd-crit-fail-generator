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
# BARVY ATRIBUTŮ
# =========================

attr_colors = {
    "Strength": "#FF6B6B",
    "Dexterity": "#6BCB77",
    "Constitution": "#FFA94D",
    "Intelligence": "#4D96FF",
    "Wisdom": "#B983FF",
    "Charisma": "#FFD93D"
}

# =========================
# CSS (KOMPAKTNÍ + CHIP STYLE)
# =========================

st.markdown("""
<style>

.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
}

/* tlačítka */
div.stButton > button {
    height: 40px;
    font-size: 14px;
    font-weight: 600;
    padding: 0 10px;
    margin: 3px;

    width: auto !important;
    min-width: unset;

    border-radius: 999px;
    white-space: nowrap;
}

/* menší mezery */
div[data-testid="stVerticalBlock"] > div {
    gap: 0.2rem;
}

h4 {
    margin-bottom: 4px;
    margin-top: 8px;
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


def generate(pool, source):
    if not pool:
        st.session_state.result = {
            "effect": "❌ Žádná data",
            "roleplay": [],
            "source": source
        }
    else:
        result = weighted_choice(pool)
        result["source"] = source
        st.session_state.result = result

    st.rerun()

# =========================
# UI
# =========================

st.title("🎲 DnD Crit Fail")

# =========================
# RESULT
# =========================

if st.session_state.result:
    r = st.session_state.result

    st.subheader("💥 Efekt")
    st.caption(f"🎯 {r.get('source')}")

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

st.markdown("---")

colA, colB, colC = st.columns(3)

# =========================
# ⚔️ ÚTOK
# =========================

with colA:
    st.subheader("⚔️ Útok")

    for attack_type, severity_dict in data.get("Útok", {}).items():
        if st.button(attack_type, key=f"attack_{attack_type}"):
            pool = severity_dict.get(st.session_state.severity)

            if not pool:
                pool = next(iter(severity_dict.values()), [])

            generate(pool, f"Útok → {attack_type} | {st.session_state.severity}")

# =========================
# 🛡️ OBRANA
# =========================

with colB:
    st.subheader("🛡️ Obrana")

    if st.button("🛡️ Obrana", key="defense_btn"):
        pool = data.get("Obrana", {}).get(st.session_state.severity)

        if not pool:
            pool = next(iter(data.get("Obrana", {}).values()), [])

        generate(pool, f"Obrana | {st.session_state.severity}")

# =========================
# 🎲 SKILLY (GRID max 2 řádky)
# =========================

with colC:
    st.subheader("🎲 Skilly")

    for attr, skills in data.get("Skill", {}).items():

        color = attr_colors.get(attr, "#FFFFFF")

        st.markdown(
            f"<h4 style='color:{color}'>{attr}</h4>",
            unsafe_allow_html=True
        )

        skills_list = list(skills.items())
        num_skills = len(skills_list)

        # max 2 řádky → spočítáme sloupce
        cols_count = (num_skills + 1) // 2

        cols = st.columns(cols_count)

        for i, (skill_name, skill_data) in enumerate(skills_list):

            col_index = i % cols_count

            pool = skill_data.get(st.session_state.severity)

            if not pool:
                pool = next(iter(skill_data.values()), [])

            if cols[col_index].button(
                skill_name,
                key=f"{attr}_{skill_name}"
            ):
                generate(
                    pool,
                    f"Skill → {attr} → {skill_name} | {st.session_state.severity}"
                )
