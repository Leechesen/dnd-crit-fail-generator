import streamlit as st
import json
import random
import os
import math
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

with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)

# =========================
# SESSION
# =========================

if "result" not in st.session_state:
    st.session_state.result = None

if "severity" not in st.session_state:
    st.session_state.severity = "Lehký"

if "last_pool" not in st.session_state:
    st.session_state.last_pool = None

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
# CSS (ULTRA KOMPAKT)
# =========================

st.markdown("""
<style>

/* minimální mezery mezi sloupci */
div[data-testid="stHorizontalBlock"] {
    gap: 0.2rem !important;
}

div[data-testid="column"] {
    padding: 2px !important;
}

/* tlačítka */
div.stButton > button {
    height: 32px;
    font-size: 13px;
    padding: 0 8px;
    border-radius: 999px;
    white-space: nowrap;
}

/* menší mezery */
div[data-testid="stVerticalBlock"] > div {
    gap: 0.1rem;
}

/* nadpisy */
h4 {
    margin: 4px 0 2px 0;
}

</style>
""", unsafe_allow_html=True)

# =========================
# GENERATE
# =========================

def weighted_choice(pool):
    return random.choice(pool)


def generate(pool, source):
    if not pool:
        st.session_state.result = {
            "effect": "❌ Žádná data",
            "roleplay": [],
            "source": source
        }
        st.session_state.last_pool = []
    else:
        result = weighted_choice(pool)
        result["source"] = source
        st.session_state.result = result
        st.session_state.last_pool = pool  # 🔥 uložíme pool

    st.rerun()

# =========================
# UI
# =========================

st.title("🎲 DnD Crit Fail")

# =========================
# RESULT + REROLL
# =========================

if st.session_state.result:

    colE1, colE2 = st.columns([4, 1])

    with colE1:
        st.subheader("💥 Efekt")

    with colE2:
        if st.session_state.get("last_pool"):
            if st.button("🔄 Generuj znovu", key="reroll"):
                pool = st.session_state.last_pool
                source = st.session_state.result.get("source", "")
                generate(pool, source)

    r = st.session_state.result

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

# layout sloupců
colA, colB, colC = st.columns([1, 1, 2])

# =========================
# ⚔️ ÚTOK
# =========================

with colA:
    st.subheader("⚔️ Útok")

    for attack_type, severity_dict in data.get("Útok", {}).items():
        if st.button(attack_type, key=f"attack_{attack_type}"):
            pool = severity_dict.get(st.session_state.severity, [])
            generate(
                pool,
                f"Útok → {attack_type} | {st.session_state.severity}"
            )

# =========================
# 🛡️ OBRANA
# =========================

with colB:
    st.subheader("🛡️ Obrana")

    if st.button("Obrana"):
        pool = data.get("Obrana", {}).get(st.session_state.severity, [])
        generate(
            pool,
            f"Obrana | {st.session_state.severity}"
        )

# =========================
# 🎲 SKILLY (MAX 2 ŘÁDKY)
# =========================

with colC:
    st.subheader("🎲 Skilly")

    for attr, skills in data.get("Skill", {}).items():

        color = attr_colors.get(attr, "#FFFFFF")

        st.markdown(
            f"<h4 style='color:{color}'>{attr}</h4>",
            unsafe_allow_html=True
        )

        items = list(skills.items())
        n = len(items)

        cols_count = math.ceil(n / 2)

        # řádek 1
        cols = st.columns(cols_count)
        for i in range(cols_count):
            if i < n:
                skill_name, skill_data = items[i]
                pool = skill_data.get(st.session_state.severity, [])

                if cols[i].button(skill_name, key=f"{attr}_{skill_name}"):
                    generate(
                        pool,
                        f"Skill → {attr} → {skill_name} | {st.session_state.severity}"
                    )

        # řádek 2
        cols = st.columns(cols_count)
        for i in range(cols_count):
            index = i + cols_count
            if index < n:
                skill_name, skill_data = items[index]
                pool = skill_data.get(st.session_state.severity, [])

                if cols[i].button(skill_name, key=f"{attr}_{skill_name}_2"):
                    generate(
                        pool,
                        f"Skill → {attr} → {skill_name} | {st.session_state.severity}"
                    )
