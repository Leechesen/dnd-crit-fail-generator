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
# ÚTOK
# =========================

with colA:
    st.subheader("⚔️ Útok")

    if st.button("Melee", key="melee_btn"):
        pool = data["Útok"].get("Melee", {}).get(st.session_state.severity, [])
        generate(pool)

    if st.button("Ranged", key="ranged_btn"):
        pool = data["Útok"].get("Ranged", {}).get(st.session_state.severity, [])
        generate(pool)

# =========================
# OBRANA / KOUZLO
# =========================

with colB:
    st.subheader("🛡️ Obrana / ✨ Kouzlo")

    if st.button("Obrana", key="obrana_btn"):
        pool = data.get("Obrana", {}).get(st.session_state.severity, [])
        generate(pool)

    if st.button("Kouzlo", key="kouzlo_btn"):
        pool = data.get("Kouzlo", {}).get(st.session_state.severity, [])
        generate(pool)

# =========================
# SKILLY (🔥 HLAVNÍ FIX)
# =========================

with colC:
    st.subheader("🎲 Skilly")

    for attr, skill_dict in data.get("Skill", {}).items():
        st.markdown(f"## {attr}")

        for skill_name, skill_data in skill_dict.items():

            # 🔹 NADPIS
            st.markdown(f"### {skill_name}")

            # 🔹 TLAČÍTKO (STEJNÝ TEXT, ALE UNIKÁTNÍ KEY)
            if st.button(
                skill_name,
                key=f"{attr}_{skill_name}"
            ):
                pool = skill_data.get(st.session_state.severity, [])
                generate(pool)

# =========================
# MANUAL REFRESH
# =========================

if st.button("🔄 Aktualizovat data z Excelu"):
    build_json_from_excel()
    st.success("Data aktualizována!")
