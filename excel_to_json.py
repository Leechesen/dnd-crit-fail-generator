import pandas as pd
import json

EXCEL_FILE = "crit_fails.xlsx"
OUTPUT_JSON = "crit_fails.json"


def normalize_severity(s):
    if not s:
        return None
    s = str(s).strip()
    if not s or s.lower() == "nan":
        return None
    return s.strip()


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

            if not severity:
                continue

            effect = str(row.get("effect", "")).strip()
            roleplay_1 = str(row.get("roleplay_1", "")).strip()
            roleplay_2 = str(row.get("roleplay_2", "")).strip()

            if not effect or effect.lower() == "nan":
                continue

            entry = {
                "effect": effect,
                "roleplay": [
                    roleplay_1 if roleplay_1.lower() != "nan" else "",
                    roleplay_2 if roleplay_2.lower() != "nan" else ""
                ],
                "weight": int(row.get("weight", 1)) if not pd.isna(row.get("weight")) else 1
            }

            # =========================
            # ÚTOK
            # =========================
            if action == "Útok":
                if not attack_type or attack_type.lower() == "nan":
                    attack_type = "Melee"

                data[action].setdefault(attack_type, {})
                data[action][attack_type].setdefault(severity, [])
                data[action][attack_type][severity].append(entry)

            # =========================
            # SKILL
            # =========================
            elif action == "Skill":
                if not attribute or attribute.lower() == "nan":
                    continue
                if not skill or skill.lower() == "nan":
                    continue

                data[action].setdefault(attribute, {})
                data[action][attribute].setdefault(skill, {})
                data[action][attribute][skill].setdefault(severity, [])
                data[action][attribute][skill][severity].append(entry)

            # =========================
            # OBRANA / OSTATNÍ
            # =========================
            else:
                data[action].setdefault(severity, [])
                data[action][severity].append(entry)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("✅ JSON vygenerován dynamicky ze všech severity nalezených v Excelu")


if __name__ == "__main__":
    build_json_from_excel()
