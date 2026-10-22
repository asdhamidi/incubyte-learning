from typing_extensions import Dict
from typing import Any
from datetime import datetime

DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y")

def _normalise_date(value):
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(value, date_format).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"unrecognised date: {value!r}")

def _missing_column(record, column_names) -> bool:
    for column_name in column_names:
        if column_name not in record:
            return True
    return False

def _trim_values(record) -> dict:
    return {
            key: value.strip() if isinstance(value, str) else value
            for key, value in record.items()
        }

def clean_record(record: Dict) -> Dict[str, Any]:
    if record == {}:
        return {}

    if _missing_column(record, column_names=["id"]):
        raise ValueError("record is missing an id")

    cleaned_record= _trim_values(record)

    if cleaned_record.get("id") in [None, ""]:
        raise ValueError("record's id is empty")

    if "date" in cleaned_record:
        cleaned_record["date"] = _normalise_date(cleaned_record["date"])
    return cleaned_record
