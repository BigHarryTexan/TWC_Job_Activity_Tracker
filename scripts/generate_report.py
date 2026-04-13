import csv
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

DATA_CSV = Path("data/work_search.csv")
REPAIRED_CSV = Path("data/work_search_repaired.csv")
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
# CSV VALIDATOR + REPAIR TOOL
# -----------------------------
def validate_and_repair_row(row):
    """Return (True, cleaned_row) or (False, reason)."""

    cleaned = {k: (v.strip() if v is not None else "") for k, v in row.items()}

    # Ensure all required fields exist
    for field in REQUIRED_FIELDS:
        if field not in cleaned:
            cleaned[field] = ""
            print(f"[REPAIR] Added missing field '{field}' to row:", cleaned)

    # Fix empty date
    if not cleaned["date"]:
        print("[REPAIR] Empty date field, skipping row:", cleaned)
        return False, "Empty date"

    # Fix invalid date formats
    try:
        datetime.strptime(cleaned["date"], "%Y-%m-%d")
    except Exception:
        print("[REPAIR] Invalid date format, skipping row:", cleaned)
        return False, "Invalid date"

    return True, cleaned

def repair_csv():
    """Reads CSV, repairs rows, writes repaired CSV."""
    repaired_rows = []

    with open(DATA_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            ok, result = validate_and_repair_row(row)
            if ok:
                repaired_rows.append(result)

    # Write repaired CSV
    with open(REPAIRED_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REQUIRED_FIELDS)
        writer.writeheader()
        writer.writerows(repaired_rows)

    print(f"[REPAIR] Repaired CSV written to {REPAIRED_CSV}")
    return repaired_rows

# -----------------------------
# LOAD + SORT ENTRIES
# -----------------------------
def load_entries():
    entries = repair_csv()  # always load repaired version

    def parse_date(d):
        return datetime.strptime(d, "%Y-%m-%d")

    entries.sort(
        key=lambda x: (
            parse_date(x["date"]),
            x["employer"].lower(),
            x.get("method", "").lower()
        )
    )

    return entries

# -----------------------------
# VIEW LAST TWO WEEKS OF CSV
# -----------------------------
def view_last_two_weeks():
    end_date = datetime.today()
    start_date = end_date - timedelta(days=13)

    entries = load_entries()

    print("\n=== LAST TWO WEEKS OF CSV ENTRIES ===\n")

    for e in entries:
        d = datetime.strptime(e["date"], "%Y-%m-%d")
        if start_date <= d <= end_date:
            print(
                f"{e['date']} | {e['employer']} | {e['position']} | "
                f"{e['method']} | {e['notes']}"
            )

    print("\n=== END ===\n")

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

def main():
    # CLI flag: view last two weeks
    if "--view" in sys.argv:
        view_last_two_weeks()
        return

    end_date = most_recent_second_monday()
    start_date = end_date - timedelta(days=13)

    entries = load_entries()

    filtered = []
    for e in entries:
        d = datetime.strptime(e["date"], "%Y-%m-%d")
        if start_date <= d <= end_date:
            filtered.append(e)

    filtered.sort(
        key=lambda x: (
            datetime.strptime(x["date"], "%Y-%m-%d"),
            x["employer"].lower(),
            x.get("method", "").lower()
        )
    )

    html = generate_html(filtered, start_date, end_date)

    output_file = REPORTS_DIR / f"twc_report_{end_date.strftime('%Y_%m_%d')}.html"
    output_file.write_text(html, encoding="utf-8")
    print(f"Report generated
