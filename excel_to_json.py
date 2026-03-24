import pandas as pd
import json

EXCEL_FILE = "crit_fails.xlsx"
OUTPUT_JSON = "crit_fails.json"

xls = pd.ExcelFile(EXCEL_FILE)
data = {}

for sheet in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet)

    action = sheet.strip()
    data[action] = {}

    for _, row in df.iterrows():

        # bezpečné načtení hodnot
        attribute = str(row.get("attribute", "")).strip()
        skill = str(row.get("skill", "")).strip()
        attack_type = str(row.get("attack_type", "")).strip()
        severity = str(row.get("severity", "")).strip()

        effect = str(row.get("effect", "")).strip()
        roleplay_1 = str(row.get("roleplay_1", "")).strip()
        roleplay_2 = str(row.get("roleplay_2", "")).strip()

        if not effect:
            continue

        entry = {
            "effect": effect,
            "roleplay": [roleplay_1, roleplay_2],
            "weight": int(row.get("weight", 1)) if not pd.isna(row.get("weight")) else 1
        }

        # =========================
        # ÚTOK
        # =========================
        if action == "Útok":

            if not attack_type:
                attack_type = "Obecný"

            if not severity:
                severity = "Normální"

            data[action].setdefault(attack_type, {})
            data[action][attack_type].setdefault(severity, [])
            data[action][attack_type][severity].append(entry)

        # =========================
        # SKILL
        # =========================
        elif action == "Skill":

            if not attribute:
                attribute = "Obecný"

            if not skill:
                skill = "Obecný"

            if not severity:
                severity = "Normální"

            data[action].setdefault(attribute, {})
            data[action][attribute].setdefault(skill, {})
            data[action][attribute][skill].setdefault(severity, [])
            data[action][attribute][skill][severity].append(entry)

        # =========================
        # OSTATNÍ (Obrana, Kouzlo…)
        # =========================
        else:

            if not severity:
                severity = "Normální"

            data[action].setdefault(severity, [])
            data[action][severity].append(entry)

# =========================
# SAVE JSON
# =========================

with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("✅ JSON byl úspěšně vygenerován")
