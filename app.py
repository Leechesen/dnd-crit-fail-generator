import streamlit as st
import json
import random

# =========================
# CONFIG + STYLY
# =========================

st.set_page_config(page_title="DnD Crit Fail", page_icon="🎲", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.2rem; padding-bottom: 1.2rem;}
.card {
    padding: 1rem 1.2rem;
    border-radius: 14px;
    border: 1px solid #2a2a2a;
    background: #111;
}
.section-title {
    font-size: 1.2rem;
    font-weight: 700;
    margin-bottom: 0.6rem;
}
.result {
    padding: 1rem;
    border-radius: 12px;
    border: 1px solid #333;
    background: #0d0d0d;
}
.badge {
    display: inline-block;
    padding: 0.25rem 0.6rem;
    border-radius: 999px;
    font-size: 0.8rem;
    margin-left: 0.5rem;
}
.green {background:#123b1a; color:#7CFF9B;}
.orange {background:#3b2a12; color:#FFB86B;}
.red {background:#3b1212; color:#FF6B6B;}
.purple {background:#2a123b; color:#D18BFF;}
button[kind="secondary"] {
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# =========================
# LOAD DATA
# =========================

with open("crit_fails.json", "r", encoding="utf-8") as f:
    data = json.load(f)

st.title("🎲 DnD Crit Fail – Combat Panel")

# =========================
# SEVERITY BAR
# =========================

sev_map = {
    "Lehký": ("green", "🟢"),
    "Střední": ("orange", "🟠"),
    "Těžký": ("red", "🔴"),
    "Sranda": ("purple", "🟣")
}

col1, col2, col3, col4 = st.columns(4)

if col1.button("🟢 Lehký"):
    st.session_state.severity = "Lehký"
if col2.button("🟠 Střední"):
    st.session_state.severity = "Střední"
if col3.button("🔴 Těžký"):
    st.session_state.severity = "Těžký"
if col4.button("🟣 Sranda"):
    st.session_state.severity = "Sranda"

severity = st.session_state.get("severity", "Lehký")

color_class, icon = sev_map[severity]

st.markdown(
    f"**Závažnost:** <span class='badge {color_class}'>{icon} {severity}</span>",
    unsafe_allow_html=True
)

st.markdown("---")

# =========================
# GENERATE FUNCTION
# =========================

def generate(pool):
    if not pool:
        st.error("❌ Žádná data")
        return

    r = random.choice(pool)

    st.markdown("<div class='result'>", unsafe_allow_html=True)
    st.markdown("### 💥 Efekt")
    st.write(r.get("effect", ""))

    st.markdown("### 🎭 Roleplay")
    rp = r.get("roleplay", [])
    if len(rp) > 0:
        st.write("• " + rp[0])
    if len(rp) > 1:
        st.write("• " + rp[1])
    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# LAYOUT – 3 SLoupce
# =========================

colA, colB, colC = st.columns([1,1,1])

# =========================
# ÚTOK
# =========================

with colA:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>⚔️ Útok</div>", unsafe_allow_html=True)

    if st.button("⚔️ Melee"):
        pool = data["Útok"].get("Melee", {}).get(severity, [])
        generate(pool)

    if st.button("🏹 Ranged"):
        pool = data["Útok"].get("Ranged", {}).get(severity, [])
        generate(pool)

    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# OBRANA / KOUZLO
# =========================

with colB:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>🛡️ Obrana / ✨ Kouzlo</div>", unsafe_allow_html=True)

    if st.button("🛡️ Obrana"):
        pool = data.get("Obrana", {}).get(severity, [])
        generate(pool)

    if st.button("✨ Kouzlo"):
        pool = data.get("Kouzlo", {}).get(severity, [])
        generate(pool)

    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# SKILLY
# =========================

with colC:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>🎲 Skilly</div>", unsafe_allow_html=True)

    for attr, skills in data.get("Skill", {}).items():
        st.markdown(f"**{attr}**")

        cols = st.columns(2)

        for i, skill in enumerate(skills):
            if cols[i % 2].button(skill):
                pool = skills.get(skill, {}).get(severity, [])
                generate(pool)

    st.markdown("</div>", unsafe_allow_html=True)
