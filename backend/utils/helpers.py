import csv
from datetime import datetime
from flask import jsonify


def get_current_date():
    """Returns today's date in YYYY-MM-DD format."""
    return datetime.now().strftime("%Y-%m-%d")


def get_current_time():
    """Returns current time in HH:MM:SS format."""
    return datetime.now().strftime("%H:%M:%S")


def export_records_to_csv(records, filename):
    """Writes list of dicts to a CSV file."""
    if not records:
        return False
    keys = records[0].keys()
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(records)
    return True


def api_response(success=True, message="", data=None, status_code=200):
    """Standardized API response helper."""
    res = {
        "success": success,
        "message": message
    }
    if data is not None:
        if isinstance(data, dict):
            res.update(data)
        else:
            res["data"] = data
    return jsonify(res), status_code
