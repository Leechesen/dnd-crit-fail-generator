import pandas as pd
import json

EXCEL_FILE = "crit_fails.xlsx"
OUTPUT_JSON = "crit_fails.json"


# =========================
# NORMALIZE SEVERITY (DYNAMIC)
# =========================
def normalize_severity(s):
    if not s or pd.isna(s):
        return "Default"
    return str(s).strip()


# =========================
# ENSURE SEVERITY EXISTS
# =========================
def ensure_severity(container, severity):
    if severity not in container:
        container[severity] = []


# =========================
# BUILD JSON
# =========================
def build_json_from_excel():
    xls = pd.ExcelFile(EXCEL_FILE)
    data = {}

    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)

        action = sheet.strip()
        data[action] = {}

        for _, row in df.iterrows():

            skill = str(row.get("skill", "")).strip()
            attribute = str(row.get("skill_category", "")).strip()
            attack_type = str(row.get("attack_type", "")).strip()
            severity = normalize_severity(row.get("severity", ""))

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
                    attack_type = "Melee"

                data[action].setdefault(attack_type, {})
                ensure_severity(data[action][attack_type], severity)
                data[action][attack_type][severity].append(entry)

            # =========================
            # SKILL
            # =========================
            elif action == "Skill":
                if not attribute or not skill:
                    continue

                data[action].setdefault(attribute, {})
                data[action][attribute].setdefault(skill, {})
                ensure_severity(data[action][attribute][skill], severity)
                data[action][attribute][skill][severity].append(entry)

            # =========================
            # OBRANA / OSTATNÍ
            # =========================
            else:
                ensure_severity(data[action], severity)
                data[action][severity].append(entry)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("✅ JSON vytvořen (dynamické severity)")


if __name__ == "__main__":
    build_json_from_excel()
