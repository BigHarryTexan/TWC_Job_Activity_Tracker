import csv
import json
from datetime import datetime, timedelta
from pathlib import Path

DATA_CSV = Path("data/work_search.csv")
REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)

def most_recent_second_monday(today=None):
    today = today or datetime.today()
    # Find most recent Monday
    offset = (today.weekday() - 0) % 7
    monday = today - timedelta(days=offset)
    # If this Monday is an "even" Monday (2nd, 4th), use it; otherwise subtract 7 days
    week_of_month = (monday.day - 1) // 7 + 1
    if week_of_month in (2, 4):
        return monday
    return monday - timedelta(days=7)

def load_entries():
    entries = []

    with open(DATA_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            entries.append(row)

    # TWC-compliant sorting: date → employer → method
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
h1 {{
    margin-bottom: 5px;
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
.signature {{
    margin-top: 40px;
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

<div class="signature">
    <p><strong>Certification:</strong> I certify that the above work search activities are true and accurate.</p>
    <p>Signature: ____________________________</p>
    <p>Date: ________________________________</p>
</div>

</body>
</html>
"""

def main():
    end_date = most_recent_second_monday()
    start_date = end_date - timedelta(days=13)

    entries = load_entries()

    filtered = [
        e for e in entries
        if start_date <= datetime.strptime(e["date"], "%Y-%m-%d") <= end_date
    ]

    # Optional but recommended: ensure filtered list stays sorted
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
    print(f"Report generated: {output_file}")

if __name__ == "__main__":
    main()
