import streamlit as st
import json
import random
import os
from excel_to_json import build_json_from_excel

EXCEL_FILE = "crit_fails.xlsx"
OUTPUT_JSON = "crit_fails.json"

# =========================
# AUTO UPDATE JSON
# =========================

if not os.path.exists(OUTPUT_JSON):
    build_json_from_excel()

elif os.path.getmtime(EXCEL_FILE) >= os.path.getmtime(OUTPUT_JSON):
    build_json_from_excel()

# =========================
# LOAD DATA
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
# ATTRIBUTE COLORS
# =========================

attr_colors = {
    "Strength": "#FF6B6B",
    "Dexterity": "#7CFF9B",
    "Constitution": "#FFB86B",
    "Intelligence": "#6BCBFF",
    "Wisdom": "#D18BFF",
    "Charisma": "#FFE66D"
}

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
        return

    new = weighted_choice(pool)

    if st.session_state.result and len(pool) > 1:
        while new == st.session_state.result:
            new = weighted_choice(pool)

    st.session_state.result = new

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

# =========================
# LAYOUT
# =========================

colA, colB, colC = st.columns(3)

# =========================
# ÚTOK
# =========================

with colA:
    st.subheader("⚔️ Útok")

    if st.button("Melee", key="melee_btn", use_container_width=True):
        pool = data["Útok"].get("Melee", {}).get(st.session_state.severity, [])
        generate(pool)

    if st.button("Ranged", key="ranged_btn", use_container_width=True):
        pool = data["Útok"].get("Ranged", {}).get(st.session_state.severity, [])
        generate(pool)

# =========================
# OBRANA / KOUZLO
# =========================

with colB:
    st.subheader("🛡️ Obrana / ✨ Kouzlo")

    if st.button("Obrana", key="obrana_btn", use_container_width=True):
        pool = data.get("Obrana", {}).get(st.session_state.severity, [])
        generate(pool)

    if st.button("Kouzlo", key="kouzlo_btn", use_container_width=True):
        pool = data.get("Kouzlo", {}).get(st.session_state.severity, [])
        generate(pool)

# =========================
# SKILLY (🔥 OPRAVENO SPRÁVNĚ)
# =========================

with colC:
    st.subheader("🎲 Skilly")

    max_cols = 3

    for attr, skills in data.get("Skill", {}).items():

        # 🔹 NADPIS ATRIBUTU
        color = attr_colors.get(attr, "#FFFFFF")
        st.markdown(
            f"<h3 style='color:{color}; margin-bottom: 5px;'>{attr}</h3>",
            unsafe_allow_html=True
        )

        skill_items = list(skills.items())

        for j in range(0, len(skill_items), max_cols):
            row = skill_items[j:j+max_cols]
            cols = st.columns(len(row))

            for i, (skill_name, skill_data) in enumerate(row):

                pool = skill_data.get(st.session_state.severity, [])

                if cols[i].button(
                    skill_name,  # ✔ správný název skillu
                    key=f"{attr}_{skill_name}",
                    use_container_width=True
                ):
                    generate(pool)

# =========================
# MANUAL REFRESH
# =========================

if st.button("🔄 Aktualizovat data z Excelu", use_container_width=True):
    build_json_from_excel()
    st.success("Data aktualizována!")
