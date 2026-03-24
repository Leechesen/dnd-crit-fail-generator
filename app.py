import streamlit as st
import json
import random

with open("crit_fails.json", "r", encoding="utf-8") as f:
    data = json.load(f)

st.set_page_config(page_title="DnD Crit Fail", page_icon="🎲")
st.title("🎲 DnD Crit Fail Generator")

def safe_get_pool(d):
    if isinstance(d, list):
        return d
    elif isinstance(d, dict):
        pool = []
        for v in d.values():
            if isinstance(v, list):
                pool += v
        return pool
    return []

action = st.selectbox("Typ akce", list(data.keys()))

pool = []
sranda_pool = []

# =========================
# ÚTOK
# =========================

if action == "Útok":
    attack_type = st.selectbox("Typ útoku", list(data["Útok"].keys()))
    attack_data = data["Útok"][attack_type]

    if isinstance(attack_data, dict):
        severity = st.selectbox("Závažnost", list(attack_data.keys()))
        pool = attack_data[severity]
        sranda_pool = attack_data.get("Sranda", [])
    else:
        pool = safe_get_pool(attack_data)

# =========================
# SKILL
# =========================

elif action == "Skill":
    attribute = st.selectbox("Atribut", list(data["Skill"].keys()))
    skill = st.selectbox("Skill", list(data["Skill"][attribute].keys()))

    skill_data = data["Skill"][attribute][skill]

    if isinstance(skill_data, dict):
        severity = st.selectbox("Závažnost", list(skill_data.keys()))
        pool = skill_data[severity]
        sranda_pool = skill_data.get("Sranda", [])
    else:
        st.warning("⚠️ Auto-fix: chybí obtížnosti")
        severity = st.selectbox("Závažnost", ["Normální"])
        pool = skill_data

# =========================
# OSTATNÍ
# =========================

else:
    other_data = data[action]

    if isinstance(other_data, dict):
        severity = st.selectbox("Závažnost", list(other_data.keys()))
        pool = other_data[severity]
        sranda_pool = other_data.get("Sranda", [])
    else:
        pool = safe_get_pool(other_data)

# =========================
# SRANDA MIX
# =========================

mix_sranda = st.checkbox("🎭 Přimíchat 'Sranda'")

if mix_sranda:
    pool = pool + sranda_pool

# =========================
# GENERATE
# =========================

if st.button("🎲 GENERUJ"):

    if not pool:
        st.error("❌ Žádná data")
    else:
        result = random.choice(pool)

        st.markdown("---")
        st.subheader("💥 Efekt")
        st.write(result.get("effect", ""))

        st.subheader("🎭 Roleplay")
        rp = result.get("roleplay", [])

        if len(rp) > 0:
            st.write(rp[0])
        if len(rp) > 1:
            st.write(rp[1])
