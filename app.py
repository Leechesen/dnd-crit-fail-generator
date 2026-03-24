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
# HELPER FUNCTION
# =========================

def get_pool_safe(d):
    """Vrátí pool bezpečně i když je struktura rozbitá"""
    if isinstance(d, list):
        return d
    elif isinstance(d, dict):
        # vezmi všechny listy uvnitř dictu
        pool = []
        for v in d.values():
            if isinstance(v, list):
                pool += v
        return pool
    return []

# =========================
# ATTACK
# =========================

if action == "Útok":
    attack_type = st.selectbox("Typ útoku", list(data["Útok"].keys()))

    attack_data = data["Útok"][attack_type]

    if isinstance(attack_data, dict):
        severity = st.selectbox("Závažnost", list(attack_data.keys()))
        pool = attack_data[severity]
    else:
        pool = get_pool_safe(attack_data)

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
    else:
        st.info("⚠️ Tento skill nemá rozdělení na obtížnosti")
        pool = get_pool_safe(skill_data)

# =========================
# OTHER (Obrana, Kouzlo…)
# =========================

else:
    other_data = data[action]

    if isinstance(other_data, dict):
        severity = st.selectbox("Závažnost", list(other_data.keys()))
        pool = other_data[severity]
    else:
        pool = get_pool_safe(other_data)

# =========================
# SRANDA MIX
# =========================

mix_sranda = st.checkbox("🎭 Mix se 'Sranda' efekty")

if mix_sranda:
    try:
        sranda_pool = []

        if action == "Útok":
            sranda_pool = data["Útok"][attack_type].get("Sranda", [])

        elif action == "Skill":
            if isinstance(skill_data, dict):
                sranda_pool = skill_data.get("Sranda", [])

        else:
            if isinstance(data[action], dict):
                sranda_pool = data[action].get("Sranda", [])

        pool = pool + sranda_pool

    except:
        pass

# =========================
# GENERATE
# =========================

if st.button("🎲 GENERUJ CRIT FAIL"):

    if not pool:
        st.warning("⚠️ Žádná data pro tuto kombinaci")
    else:
        result = random.choice(pool)

        st.markdown("---")

        st.subheader("💥 Herní efekt")
        st.write(result.get("effect", "—"))

        st.subheader("🎭 Roleplay (DM říká)")
        roleplay = result.get("roleplay", [])

        if len(roleplay) > 0:
            st.write(roleplay[0])
        if len(roleplay) > 1:
            st.write(roleplay[1])
