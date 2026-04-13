import json
import pandas as pd
from datetime import datetime, timedelta
from dateutil import parser

# ---------------------------------------------------------
# Load merged data
# ---------------------------------------------------------

def load_merged(path="merged.json"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                return []
            return data
    except Exception:
        return []


# ---------------------------------------------------------
# Filter last 14 days
# ---------------------------------------------------------

def filter_last_two_weeks(entries):
    now = datetime.now().date()
    start = now - timedelta(days=13)

    filtered = []
    for e in entries:
        try:
            d = parser.parse(e["date"]).date()
        except Exception:
            continue
        if start <= d <= now:
            filtered.append(e)

    return filtered


# ---------------------------------------------------------
# Generate HTML report
# ---------------------------------------------------------

def generate_html(entries, output="report.html"):
    df = pd.DataFrame(entries)

    if df.empty:
        html_table = "<p>No entries found for the last two weeks.</p>"
    else:
        df = df.sort_values("date")
        html_table = df.to_html(
            index=False,
            escape=False,
            justify="left",
            border=0,
            classes="twc-table"
        )

    today = datetime.now().strftime("%B %d, %Y")

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>TWC Work Search Report</title>
<style>
  body {{
    font-family: Arial, sans-serif;
    margin: 40px;
    line-height: 1.5;
  }}
  h1 {{
    text-align: center;
    margin-bottom: 10px;
  }}
  h2 {{
    margin-top: 40px;
  }}
  .twc-table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 20px;
  }}
  .twc-table th, .twc-table td {{
    border: 1px solid #ccc;
    padding: 8px;
    text-align: left;
  }}
  .twc-table th {{
    background: #f0f0f0;
  }}
</style>
</head>
<body>

<h1>Texas Workforce Commission<br>Work Search Log</h1>
<p><strong>Report Date:</strong> {today}</p>
<p><strong>Period Covered:</strong> Last 14 Days</p>

<h2>Work Search Activities</h2>
{html_table}

</body>
</html>
"""

    with open(output, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Report written to {output}")


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():
    print("Loading merged.json...")
    merged = load_merged()

    print("Filtering last 14 days...")
    filtered = filter_last_two_weeks(merged)

    print("Generating HTML report...")
    generate_html(filtered)

    print("Done.")


if __name__ == "__main__":
    main()
