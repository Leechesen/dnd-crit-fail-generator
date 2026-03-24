import streamlit as st
import json
import random

# =========================
# LOAD JSON
# =========================

with open("crit_fails.json", "r", encoding="utf-8") as f:
    data = json.load(f)

st.title("🎲 DnD Crit Fail Generátor")

# =========================
# MÓD VÝBĚRU
# =========================

mode = st.selectbox(
    "Režim generování:",
    ["Normální", "Sranda", "Mix"]
)

mix_ratio = 0

if mode == "Mix":
    mix_ratio = st.slider(
        "Kolik % Sranda:",
        0, 100, 20
    )

# =========================
# VÝBĚR TYP AKCE
# =========================

typ_akce = st.selectbox("Vyber typ akce:", list(data.keys()))

moznosti_normal = []
moznosti_sranda = []

# =========================
# ÚTOK
# =========================

if typ_akce == "Útok":

    attack_type = st.selectbox(
        "Typ útoku:",
        list(data["Útok"].keys())
    )

    severity_list = list(data["Útok"][attack_type].keys())

    if "Sranda" in severity_list:
        moznosti_sranda = data["Útok"][attack_type]["Sranda"]

    normal_severities = [s for s in severity_list if s != "Sranda"]

    severity = st.selectbox(
        "Závažnost:",
        normal_severities
    )

    moznosti_normal = data["Útok"][attack_type][severity]

# =========================
# SKILL
# =========================

elif typ_akce == "Skill":

    skill = st.selectbox(
        "Atribut:",
        list(data["Skill"].keys())
    )

    category = st.selectbox(
        "Skill:",
        list(data["Skill"][skill].keys())
    )

    severity_list = list(data["Skill"][skill][category].keys())

    if "Sranda" in severity_list:
        moznosti_sranda = data["Skill"][skill][category]["Sranda"]

    normal_severities = [s for s in severity_list if s != "Sranda"]

    severity = st.selectbox(
        "Závažnost:",
        normal_severities
    )

    moznosti_normal = data["Skill"][skill][category][severity]

# =========================
# OSTATNÍ
# =========================

else:

    severity_list = list(data[typ_akce].keys())

    if "Sranda" in severity_list:
        moznosti_sranda = data[typ_akce]["Sranda"]

    normal_severities = [s for s in severity_list if s != "Sranda"]

    severity = st.selectbox(
        "Závažnost:",
        normal_severities
    )

    moznosti_normal = data[typ_akce][severity]

# =========================
# GENEROVÁNÍ
# =========================

if st.button("🎲 Generuj výsledek"):

    vysledek = None

    if mode == "Normální":
        vysledek = random.choice(moznosti_normal)

    elif mode == "Sranda":
        if moznosti_sranda:
            vysledek = random.choice(moznosti_sranda)
        else:
            st.warning("⚠️ Pro tuto kategorii nejsou žádné Sranda výsledky")
            vysledek = random.choice(moznosti_normal)

    elif mode == "Mix":

        if moznosti_sranda and random.randint(1, 100) <= mix_ratio:
            vysledek = random.choice(moznosti_sranda)
        else:
            vysledek = random.choice(moznosti_normal)

    # =========================
    # VÝPIS
    # =========================

    st.divider()

    st.subheader("📉 Herní efekt")
    st.write(vysledek["effect"])

    st.write("")

    st.subheader("🎭 Roleplay")
    st.write(vysledek["roleplay"][0])
    st.write(vysledek["roleplay"][1])
