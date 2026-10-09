# Data notes

The project contains two CSV files:

- `raw/maintenance_requests_raw.csv` — 3,200 synthetic records, including one duplicate request ID and small text inconsistencies for cleaning practice.
- `processed/maintenance_requests_clean.csv` — 3,199 cleaned records with derived timing and SLA fields.

No personal names, phone numbers, room occupants, addresses, or official NJIT records are included. Hall names are fictionalized for portfolio use.

Run `python src/generate_data.py` followed by `python src/analyze.py` to regenerate both files.
