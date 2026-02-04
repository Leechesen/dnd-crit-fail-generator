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
        if pd.isna(row.get("severity")) or pd.isna(row.get("effect")):
            continue

        entry = {
            "effect": str(row["effect"]).strip(),
            "roleplay": [
                str(row["roleplay_1"]).strip(),
                str(row["roleplay_2"]).strip()
            ],
            "weight": int(row["weight"]) if not pd.isna(row.get("weight")) else 1
        }

        if action == "Útok":
            attack_type = str(row["attack_type"]).strip()
            severity = str(row["severity"]).strip()

            data[action].setdefault(attack_type, {})
            data[action][attack_type].setdefault(severity, [])
            data[action][attack_type][severity].append(entry)
        else:
            severity = str(row["severity"]).strip()
            data[action].setdefault(severity, [])
            data[action][severity].append(entry)

with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("JSON vygenerován z Excelu")
