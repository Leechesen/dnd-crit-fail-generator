import streamlit as st
import json
import random

# =========================
# LOAD JSON
# =========================

with open("crit_fails.json", "r", encoding="utf-8") as f:
    data = json.load(f)

st.title("🎲 DnD Crit Fail Generator")

# =========================
# TYPE OF ACTION
# =========================

action = st.selectbox("Typ akce", list(data.keys()))

# =========================
# ATTACK
# =========================

if action == "Útok":
    attack_type = st.selectbox("Typ útoku", list(data["Útok"].keys()))
    severity = st.selectbox("Závažnost", list(data["Útok"][attack_type].keys()))

    pool = data["Útok"][attack_type][severity]

# =========================
# SKILL
# =========================

elif action == "Skill":
    attribute = st.selectbox("Atribut", list(data["Skill"].keys()))
    skill = st.selectbox("Skill", list(data["Skill"][attribute].keys()))
    severity = st.selectbox("Závažnost", list(data["Skill"][attribute][skill].keys()))

    pool = data["Skill"][attribute][skill][severity]

# =========================
# OTHER (Obrana, Kouzlo…)
# =========================

else:
    severity = st.selectbox("Závažnost", list(data[action].keys()))
    pool = data[action][severity]

# =========================
# SRANDA MIX TOGGLE
# =========================

mix_sranda = st.checkbox("🎭 Mix se 'Sranda' efekty")

if mix_sranda:
    try:
        if action == "Útok":
            sranda_pool = data["Útok"][attack_type].get("Sranda", [])
        elif action == "Skill":
            sranda_pool = data["Skill"][attribute][skill].get("Sranda", [])
        else:
            sranda_pool = data[action].get("Sranda", [])

        pool = pool + sranda_pool
    except:
        pass

# =========================
# GENERATE BUTTON
# =========================

if st.button("🎲 GENERUJ CRIT FAIL"):

    if not pool:
        st.warning("⚠️ Žádná data pro tuto kombinaci")
    else:
        result = random.choice(pool)

        st.markdown("---")

        st.subheader("💥 Herní efekt")
        st.write(result["effect"])

        st.subheader("🎭 Roleplay (DM říká)")
        st.write(result["roleplay"][0])
        st.write(result["roleplay"][1])
