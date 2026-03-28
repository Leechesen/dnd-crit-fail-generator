import streamlit as st
import json
import random

# =========================
# CONFIG
# =========================

st.set_page_config(page_title="DnD Crit Fail", page_icon="🎲", layout="wide")

# =========================
# LOAD DATA
# =========================

with open("crit_fails.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# =========================
# SESSION STATE
# =========================

if "result" not in st.session_state:
    st.session_state.result = None

if "severity" not in st.session_state:
    st.session_state.severity = "Lehký"

# =========================
# STYLY
# =========================

st.markdown("""
<style>
.result-box {
    padding: 1rem;
    border-radius: 12px;
    border: 1px solid #333;
    background: #111;
}
.green {color:#7CFF9B;}
.orange {color:#FFB86B;}
.red {color:#FF6B6B;}
.purple {color:#D18BFF;}
</style>
""", unsafe_allow_html=True)

# =========================
# TITLE
# =========================

st.title("🎲 DnD Crit Fail")

# =========================
# RESULT (NAHOŘE)
# =========================

if st.session_state.result:
    r = st.session_state.result

    st.markdown("<div class='result-box'>", unsafe_allow_html=True)

    st.subheader("💥 Efekt")
    st.write(r.get("effect", ""))

    st.subheader("🎭 Roleplay")
    rp = r.get("roleplay", [])
    if len(rp) > 0:
        st.write("• " + rp[0])
    if len(rp) > 1:
        st.write("• " + rp[1])

    st.markdown("</div>", unsafe_allow_html=True)

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

st.write(f"Závažnost: **{st.session_state.severity}**")

st.markdown("---")

# =========================
# GENERATE FUNCTION
# =========================

def generate(pool):
    if not pool:
        st.session_state.result = {"effect": "❌ Žádná data", "roleplay": []}
    else:
        st.session_state.result = random.choice(pool)

# =========================
# LAYOUT
# =========================

colA, colB, colC = st.columns(3)

# =========================
# ÚTOK
# =========================

with colA:
    st.subheader("⚔️ Útok")

    if st.button("⚔️ Melee"):
        pool = data["Útok"].get("Melee", {}).get(st.session_state.severity, [])
        generate(pool)

    if st.button("🏹 Ranged"):
        pool = data["Útok"].get("Ranged", {}).get(st.session_state.severity, [])
        generate(pool)

# =========================
# OBRANA / KOUZLO
# =========================

with colB:
    st.subheader("🛡️ Obrana / ✨ Kouzlo")

    if st.button("🛡️ Obrana"):
        pool = data.get("Obrana", {}).get(st.session_state.severity, [])
        generate(pool)

    if st.button("✨ Kouzlo"):
        pool = data.get("Kouzlo", {}).get(st.session_state.severity, [])
        generate(pool)

# =========================
# SKILLY
# =========================

with colC:
    st.subheader("🎲 Skilly")

    for attr, skills in data.get("Skill", {}).items():
        st.markdown(f"**{attr}**")

        cols = st.columns(2)

        for i, skill in enumerate(skills):
            if cols[i % 2].button(skill):
                pool = skills.get(skill, {}).get(st.session_state.severity, [])
                generate(pool)
