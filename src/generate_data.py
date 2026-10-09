"""Generate the synthetic residence-hall maintenance request dataset.

This project intentionally uses synthetic, fictionalized data so the repository
can be shared publicly without exposing resident or university information.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "maintenance_requests_raw.csv"
SEED = 42


HALLS = [
    "Laurel Hall",
    "Oak Hall",
    "Maple Hall",
    "Cedar Hall",
    "Talbott Hall",
    "Riverfront Hall",
]

HALL_WEIGHTS = [0.19, 0.17, 0.16, 0.15, 0.18, 0.15]

ISSUE_PROFILES = {
    "Plumbing": [
        ("Toilet", 0.30),
        ("Sink or faucet", 0.24),
        ("Leak", 0.22),
        ("Shower", 0.14),
        ("Drain", 0.10),
    ],
    "HVAC": [
        ("Heating", 0.32),
        ("Air conditioning", 0.28),
        ("Thermostat", 0.20),
        ("Ventilation", 0.12),
        ("Noise", 0.08),
    ],
    "Electrical": [
        ("Light fixture", 0.34),
        ("Outlet", 0.28),
        ("Breaker", 0.17),
        ("Appliance", 0.13),
        ("Other electrical", 0.08),
    ],
    "Furniture": [
        ("Bed frame", 0.30),
        ("Desk", 0.24),
        ("Chair", 0.21),
        ("Drawer", 0.14),
        ("Other furniture", 0.11),
    ],
    "Access": [
        ("Room lock", 0.38),
        ("Key or card", 0.30),
        ("Exterior door", 0.17),
        ("Mailbox", 0.08),
        ("Other access", 0.07),
    ],
    "Cleanliness": [
        ("Trash or recycling", 0.34),
        ("Pest concern", 0.24),
        ("Spill or odor", 0.18),
        ("Common-area cleaning", 0.16),
        ("Other cleanliness", 0.08),
    ],
    "Safety": [
        ("Smoke detector", 0.30),
        ("Emergency light", 0.20),
        ("Trip hazard", 0.18),
        ("Fire extinguisher", 0.17),
        ("Other safety", 0.15),
    ],
    "Internet": [
        ("Wi-Fi connection", 0.48),
        ("Ethernet port", 0.20),
        ("Network outage", 0.18),
        ("Device registration", 0.14),
    ],
    "Other": [
        ("Room condition", 0.40),
        ("Paint or wall", 0.25),
        ("Window or shade", 0.20),
        ("Other request", 0.15),
    ],
}

CATEGORY_WEIGHTS = {
    "Plumbing": 0.22,
    "HVAC": 0.16,
    "Electrical": 0.14,
    "Furniture": 0.13,
    "Access": 0.11,
    "Cleanliness": 0.10,
    "Safety": 0.05,
    "Internet": 0.06,
    "Other": 0.03,
}

TEAM_BY_CATEGORY = {
    "Plumbing": "Facilities",
    "HVAC": "Facilities",
    "Electrical": "Facilities",
    "Furniture": "Facilities",
    "Access": "Access Services",
    "Cleanliness": "Custodial",
    "Safety": "Safety Team",
    "Internet": "IT Support",
    "Other": "Facilities",
}

ASSIGNMENT_BASE_HOURS = {
    "Emergency": 0.8,
    "High": 2.4,
    "Medium": 5.4,
    "Low": 7.5,
}

RESOLUTION_BASE_HOURS = {
    "Plumbing": 19,
    "HVAC": 28,
    "Electrical": 15,
    "Furniture": 39,
    "Access": 7,
    "Cleanliness": 9,
    "Safety": 4,
    "Internet": 11,
    "Other": 24,
}

DESCRIPTION_TEMPLATES = {
    "Plumbing": "Resident reported a {subcategory} concern in a residential area.",
    "HVAC": "Resident reported a {subcategory} issue affecting comfort.",
    "Electrical": "Resident reported a {subcategory} issue and requested inspection.",
    "Furniture": "Resident reported a {subcategory} problem with room furniture.",
    "Access": "Resident reported a {subcategory} access issue.",
    "Cleanliness": "Resident reported a {subcategory} concern in a shared space.",
    "Safety": "Resident reported a {subcategory} concern requiring review.",
    "Internet": "Resident reported a {subcategory} connectivity issue.",
    "Other": "Resident submitted a general facilities request.",
}


def _weighted_choice(rng: np.random.Generator, values: list[str], probabilities: list[float], size: int) -> np.ndarray:
    return rng.choice(values, size=size, p=probabilities)


def _random_submission_times(rng: np.random.Generator, n: int) -> pd.DatetimeIndex:
    """Create a year of submissions with realistic move-in and winter spikes."""

    month_starts = pd.date_range("2025-09-01", periods=12, freq="MS")
    month_weights = np.array([0.14, 0.07, 0.06, 0.07, 0.07, 0.06, 0.08, 0.07, 0.06, 0.07, 0.10, 0.15])
    month_indexes = rng.choice(np.arange(12), size=n, p=month_weights / month_weights.sum())
    timestamps: list[pd.Timestamp] = []
    for month_index in month_indexes:
        month_start = month_starts[month_index]
        days_in_month = month_start.days_in_month
        day_offset = int(rng.integers(0, days_in_month))
        minute_offset = int(rng.integers(0, 24 * 60))
        timestamps.append(month_start + pd.Timedelta(days=day_offset, minutes=minute_offset))
    return pd.DatetimeIndex(timestamps)


def _weighted_subcategories(rng: np.random.Generator, categories: np.ndarray) -> list[str]:
    subcategories: list[str] = []
    for category in categories:
        options, probabilities = zip(*ISSUE_PROFILES[str(category)])
        subcategories.append(str(rng.choice(options, p=probabilities)))
    return subcategories


def generate_dataset(n_unique: int = 3199) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    submitted_at = _random_submission_times(rng, n_unique)
    categories = _weighted_choice(
        rng,
        list(CATEGORY_WEIGHTS),
        list(CATEGORY_WEIGHTS.values()),
        n_unique,
    )
    subcategories = _weighted_subcategories(rng, categories)
    priorities = _weighted_choice(rng, ["Emergency", "High", "Medium", "Low"], [0.07, 0.22, 0.51, 0.20], n_unique)
    halls = _weighted_choice(rng, HALLS, HALL_WEIGHTS, n_unique)
    resident_types = _weighted_choice(rng, ["Resident", "Resident Assistant", "Staff"], [0.78, 0.16, 0.06], n_unique)
    sources = _weighted_choice(rng, ["Resident portal", "Front desk", "RA referral", "Phone", "Email"], [0.48, 0.21, 0.16, 0.09, 0.06], n_unique)

    rows: list[dict[str, object]] = []
    for index in range(n_unique):
        category = str(categories[index])
        priority = str(priorities[index])
        submitted = submitted_at[index]
        # Requests submitted overnight or on weekends wait longer for routing.
        routing_penalty = 1.2 if submitted.dayofweek >= 5 else 0.0
        routing_penalty += 1.0 if submitted.hour < 7 or submitted.hour >= 22 else 0.0
        assignment_hours = max(
            0.15,
            float(rng.normal(ASSIGNMENT_BASE_HOURS[priority] + routing_penalty, 0.9 if priority != "Low" else 1.8)),
        )
        assigned = submitted + pd.Timedelta(hours=assignment_hours)

        status = str(rng.choice(["Resolved", "Open", "Cancelled"], p=[0.952, 0.038, 0.010]))
        first_response = assigned + pd.Timedelta(hours=max(0.1, float(rng.normal(0.8, 0.35))))
        resolution_hours = max(1.0, float(rng.lognormal(np.log(RESOLUTION_BASE_HOURS[category]), 0.48)))
        resolved = first_response + pd.Timedelta(hours=resolution_hours) if status == "Resolved" else pd.NaT

        # Emergency and high-priority requests tend to be in rooms; other work
        # can also come from common areas and building entrances.
        if category in {"Cleanliness", "Safety", "Access"} and rng.random() < 0.28:
            room_area = str(rng.choice(["Lobby", "Laundry room", "Hallway", "Common room", "Building entrance"]))
            floor = "Common area"
        else:
            floor_number = int(rng.integers(1, 11))
            room_area = f"Room {floor_number}{int(rng.integers(1, 31)):02d}"
            floor = str(floor_number)

        satisfaction = ""
        if status == "Resolved":
            score = 4.55 - max(resolution_hours - 24, 0) / 65 - max(assignment_hours - 4, 0) / 10 + rng.normal(0, 0.55)
            satisfaction = int(np.clip(np.rint(score), 1, 5))

        base_cost = {
            "Plumbing": 115,
            "HVAC": 240,
            "Electrical": 165,
            "Furniture": 180,
            "Access": 90,
            "Cleanliness": 75,
            "Safety": 125,
            "Internet": 55,
            "Other": 110,
        }[category]
        estimated_cost = round(max(0, float(rng.lognormal(np.log(base_cost), 0.45))), 2)
        reopened = "Yes" if status == "Resolved" and rng.random() < (0.15 if category in {"HVAC", "Plumbing"} else 0.08) else "No"

        rows.append(
            {
                "request_id": f"MNT-{index + 1:05d}",
                "submitted_at": submitted.strftime("%Y-%m-%d %H:%M:%S"),
                "residence_hall": str(halls[index]),
                "floor": floor,
                "room_or_area": room_area,
                "category": category,
                "subcategory": subcategories[index],
                "priority": priority,
                "status": status,
                "assigned_team": TEAM_BY_CATEGORY[category],
                "source": str(sources[index]),
                "resident_type": str(resident_types[index]),
                "assigned_at": assigned.strftime("%Y-%m-%d %H:%M:%S"),
                "first_response_at": first_response.strftime("%Y-%m-%d %H:%M:%S"),
                "resolved_at": "" if pd.isna(resolved) else resolved.strftime("%Y-%m-%d %H:%M:%S"),
                "estimated_cost_usd": estimated_cost,
                "satisfaction_score": satisfaction,
                "reopened": reopened,
                "description": DESCRIPTION_TEMPLATES[category].format(subcategory=subcategories[index]),
            }
        )

    frame = pd.DataFrame(rows)
    # Add one exact duplicate so the cleaning workflow has a visible quality check.
    frame = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
    # Add two harmless text inconsistencies for the cleaning step to standardize.
    frame.loc[6, "category"] = " plumbing "
    frame.loc[12, "assigned_team"] = "facilities"
    return frame


def main() -> None:
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    frame = generate_dataset()
    frame.to_csv(RAW_PATH, index=False)
    print(f"Wrote {len(frame):,} raw records to {RAW_PATH}")


if __name__ == "__main__":
    main()
