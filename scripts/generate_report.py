import csv
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

DATA_CSV = Path("data/work_search.csv")
REPAIRED_CSV = Path("data/work_search_repaired.csv")
JSON_PATH = Path("data/work_search.json")
JSON_REPAIRED = Path("data/work_search_repaired.json")
REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)

REQUIRED_FIELDS = ["timestamp", "date", "employer", "position", "method", "notes"]

def most_recent_second_monday(today=None):
    today = today or datetime.today()
    offset = (today.weekday() - 0) % 7
    monday = today - timedelta(days=offset)
    week_of_month = (monday.day - 1) // 7 + 1
    if week_of_month in (2, 4):
        return monday
    return monday - timedelta(days=7)

# -----------------------------
# CSV REPAIR
# -----------------------------
def validate_and_repair_csv_row(row):
    cleaned = {k: (v.strip() if v is not None else "") for k, v in row.items()}

    for field in REQUIRED_FIELDS:
        if field not in cleaned:
            cleaned[field] = ""
            print(f"[CSV REPAIR] Added missing field '{field}' to row:", cleaned)

    if not cleaned["date"]:
        print("[CSV REPAIR] Empty date field, skipping row:", cleaned)
        return False, "Empty date"

    try:
        datetime.strptime(cleaned["date"], "%Y-%m-%d")
    except Exception:
        print("[CSV REPAIR] Invalid date format, skipping row:", cleaned)
        return False, "Invalid date"

    try:
        cleaned["timestamp"] = int(cleaned["timestamp"])
    except Exception:
        cleaned["timestamp"] = 0

    return True, cleaned

def repair_csv():
    repaired_rows = []

    if not DATA_CSV.exists():
        print("[CSV] No CSV file found.")
        return repaired_rows

    with open(DATA_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ok, result = validate_and_repair_csv_row(row)
            if ok:
                repaired_rows.append(result)

    with open(REPAIRED_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REQUIRED_FIELDS)
        writer.writeheader()
        writer.writerows(repaired_rows)

    print(f"[CSV REPAIR] Repaired CSV written to {REPAIRED_CSV}")
    return repaired_rows

# -----------------------------
# JSON REPAIR
# -----------------------------
def repair_json():
    if not JSON_PATH.exists():
        print("[JSON] No JSON file found, skipping JSON repair.")
        return []

    try:
        raw = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        print("[JSON] Failed to parse JSON:", e)
        return []

    repaired = []
    for entry in raw:
        fixed = {}
        for field in REQUIRED_FIELDS:
            fixed[field] = entry.get(field, "")

        fixed = {k: (v.strip() if isinstance(v, str) else v) for k, v in fixed.items()}

        try:
            datetime.strptime(fixed["date"], "%Y-%m-%d")
        except Exception:
            print("[JSON REPAIR] Invalid date, skipping:", fixed)
            continue

        try:
            fixed["timestamp"] = int(fixed["timestamp"])
        except Exception:
            fixed["timestamp"] = 0

        repaired.append(fixed)

    JSON_REPAIRED.write_text(json.dumps(repaired, indent=2), encoding="utf-8")
    print(f"[JSON REPAIR] Repaired JSON written to {JSON_REPAIRED}")
    return repaired

# -----------------------------
# UNIFIED LOADER (CSV + JSON)
# -----------------------------
def load_data():
    csv_entries = repair_csv()
    json_entries = repair_json()

    json_index = {e["timestamp"]: e for e in json_entries}
    merged = []

    for row in csv_entries:
        ts = row["timestamp"]
        if ts in json_index:
            j = json_index[ts]
            merged.append({
                "timestamp": ts,
                "date": row["date"],
                "employer": row["employer"],
                "position": row["position"],
                "method": row["method"],
                "notes": row["notes"] or j.get("notes", "")
            })
        else:
            merged.append(row)

    existing_ts = {e["timestamp"] for e in merged}
    for ts, j in json_index.items():
        if ts not in existing_ts:
            merged.append(j)

    merged.sort(
        key=lambda x: (
            datetime.strptime(x["date"], "%Y-%m-%d"),
            x["employer"].lower(),
            x["method"].lower()
        )
    )

    return merged

# -----------------------------
# VIEW LAST TWO WEEKS (CLI)
# -----------------------------
def view_last_two_weeks_cli():
    end_date = datetime.today()
    start_date = end_date - timedelta(days=13)
    entries = load_data()

    print("\n=== LAST TWO WEEKS OF ENTRIES (MERGED CSV+JSON) ===\n")
    for e in entries:
        d = datetime.strptime(e["date"], "%Y-%m-%d")
        if start_date <= d <= end_date:
            print(
                f"{e['date']} | {e['employer']} | {e['position']} | "
                f"{e['method']} | {e['notes']}"
            )
    print("\n=== END ===\n")

# -----------------------------
# HTML REPORT
# -----------------------------
def truncate(text, length=60):
    return text if len(text) <= length else text[:length] + "…"

def generate_html(entries, start_date, end_date):
    rows = ""
    for e in entries:
        rows += f"""
        <tr>
            <td>{e['date']}</td>
            <td>{e['employer']}</td>
            <td>{e['position']}</td>
            <td>{e['method']}</td>
            <td>{truncate(e['notes'])}</td>
        </tr>
        """

    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>TWC Work Search Report</title>
<style>
body {{
    font-family: Arial, sans-serif;
    margin: 40px;
}}
table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 20px;
}}
th, td {{
    border: 1px solid #333;
    padding: 8px;
    font-size: 14px;
}}
th {{
    background: #f0f0f0;
}}
</style>
</head>
<body>

<h1>Texas Workforce Commission – Work Search Report</h1>
<p><strong>Reporting Period:</strong> {start_date.strftime("%Y-%m-%d")} to {end_date.strftime("%Y-%m-%d")}</p>

<table>
    <tr>
        <th>Date</th>
        <th>Employer</th>
        <th>Position</th>
        <th>Method</th>
        <th>Notes</th>
    </tr>
    {rows}
</table>

</body>
</html>
"""

# -----------------------------
# INTEGRITY CHECK
# -----------------------------
def integrity_check():
    entries = load_data()
    print(f"[INTEGRITY] Total merged entries: {len(entries)}")
    bad = []
    for e in entries:
        try:
            datetime.strptime(e["date"], "%Y-%m-%d")
        except Exception:
            bad.append(e)
    if bad:
        print("[INTEGRITY] Entries with bad dates:")
        for b in bad:
            print(b)
    else:
        print("[INTEGRITY] All dates valid.")

# -----------------------------
# MAIN
# -----------------------------
def main():
    if "--view" in sys.argv:
        view_last_two_weeks_cli()
        return

    if "--check" in sys.argv:
        integrity_check()
        return

    end_date = most_recent_second_monday()
    start_date = end_date - timedelta(days=13)

    entries = load_data()

    filtered = [
        e for e in entries
        if start_date <= datetime.strptime(e["date"], "%Y-%m-%d") <= end_date
    ]

    filtered.sort(
        key=lambda x: (
            datetime.strptime(x["date"], "%Y-%m-%d"),
            x["employer"].lower(),
            x["method"].lower()
        )
    )

    html = generate_html(filtered, start_date, end_date)
    output_file = REPORTS_DIR / f"twc_report_{end_date.strftime('%Y_%m_%d')}.html"
    output_file.write_text(html, encoding="utf-8")
    print(f"Report generated: {output_file}")

if __name__ == "__main__":
    main()
