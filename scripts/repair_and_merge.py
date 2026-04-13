import json
import pandas as pd
from dateutil import parser
from datetime import datetime

# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def clean_date(value):
    """Return ISO date or None."""
    if not value or str(value).strip() == "":
        return None
    try:
        return parser.parse(value).date().isoformat()
    except Exception:
        return None

def clean_text(value):
    if value is None:
        return ""
    return str(value).strip()

def load_raw_csv(path="raw.csv"):
    """Load raw CSV into a DataFrame, repairing rows."""
    try:
        df = pd.read_csv(path, header=None, names=[
            "timestamp", "date", "employer", "position", "method", "notes"
        ], dtype=str)
    except Exception:
        return pd.DataFrame(columns=[
            "timestamp", "date", "employer", "position", "method", "notes"
        ])

    # Clean fields
    df["timestamp"] = df["timestamp"].apply(lambda x: int(x) if str(x).isdigit() else None)
    df["date"] = df["date"].apply(clean_date)
    df["employer"] = df["employer"].apply(clean_text)
    df["position"] = df["position"].apply(clean_text)
    df["method"] = df["method"].apply(clean_text)
    df["notes"] = df["notes"].apply(clean_text)

    # Drop rows missing critical fields
    df = df.dropna(subset=["timestamp", "date", "employer", "position", "method"])

    return df


def load_raw_json(path="raw.json"):
    """Load raw JSON list and repair entries."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = []

    repaired = []
    for entry in data:
        ts = entry.get("timestamp")
        try:
            ts = int(ts)
        except Exception:
            continue

        repaired.append({
            "timestamp": ts,
            "date": clean_date(entry.get("date")),
            "employer": clean_text(entry.get("employer")),
            "position": clean_text(entry.get("position")),
            "method": clean_text(entry.get("method")),
            "notes": clean_text(entry.get("notes")),
        })

    # Drop entries missing critical fields
    repaired = [
        e for e in repaired
        if e["timestamp"] and e["date"] and e["employer"] and e["position"] and e["method"]
    ]

    return repaired


# ---------------------------------------------------------
# Merge Logic (Option B)
# ---------------------------------------------------------

def merge_csv_json(csv_df, json_list):
    """Merge repaired CSV and JSON into a unified dataset."""

    # Convert CSV to dict list
    csv_list = csv_df.to_dict(orient="records")

    # Index JSON by timestamp for quick lookup
    json_by_ts = {e["timestamp"]: e for e in json_list}

    merged = []

    # Start with CSV entries (CSV wins audit-critical fields)
    for row in csv_list:
        ts = row["timestamp"]
        if ts in json_by_ts:
            j = json_by_ts[ts]
            merged.append({
                "timestamp": ts,
                "date": row["date"],        # CSV wins
                "employer": row["employer"],# CSV wins
                "position": row["position"],# CSV wins
                "method": row["method"],    # CSV wins
                "notes": j.get("notes") or row.get("notes") or ""
            })
        else:
            merged.append(row)

    # Add JSON-only entries
    csv_ts = {r["timestamp"] for r in csv_list}
    for entry in json_list:
        if entry["timestamp"] not in csv_ts:
            merged.append(entry)

    # Sort by timestamp
    merged.sort(key=lambda x: x["timestamp"])

    return merged


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():
    print("Loading raw CSV...")
    csv_df = load_raw_csv()

    print("Loading raw JSON...")
    json_list = load_raw_json()

    print("Merging...")
    merged = merge_csv_json(csv_df, json_list)

    # Write repaired CSV
    print("Writing repaired.csv...")
    csv_df.to_csv("repaired.csv", index=False, header=False)

    # Write repaired JSON
    print("Writing repaired.json...")
    with open("repaired.json", "w", encoding="utf-8") as f:
        json.dump(json_list, f, indent=2)

    # Write merged JSON
    print("Writing merged.json...")
    with open("merged.json", "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2)

    print("Done.")


if __name__ == "__main__":
    main()
