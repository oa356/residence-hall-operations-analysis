"""Clean, analyze, and export the residence-hall maintenance project outputs."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "maintenance_requests_raw.csv"
PROCESSED_PATH = ROOT / "data" / "processed" / "maintenance_requests_clean.csv"
REPORTS_DIR = ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
TABLES_DIR = REPORTS_DIR / "tables"
EXCEL_PATH = ROOT / "dashboard" / "maintenance_operations_dashboard.xlsx"

SLA_TARGETS = {"Emergency": 1.0, "High": 4.0, "Medium": 8.0, "Low": 24.0}
COLOR = "#2563eb"
NAVY = "#0f172a"
MUTED = "#64748b"
GREEN = "#059669"
ORANGE = "#ea580c"


def _ensure_directories() -> None:
    for directory in [PROCESSED_PATH.parent, REPORTS_DIR, FIGURES_DIR, TABLES_DIR, EXCEL_PATH.parent]:
        directory.mkdir(parents=True, exist_ok=True)


def clean_data(frame: pd.DataFrame) -> pd.DataFrame:
    cleaned = frame.copy()
    cleaned.columns = [column.strip().lower() for column in cleaned.columns]

    text_columns = [
        "request_id",
        "residence_hall",
        "floor",
        "room_or_area",
        "category",
        "subcategory",
        "priority",
        "status",
        "assigned_team",
        "source",
        "resident_type",
        "reopened",
        "description",
    ]
    for column in text_columns:
        cleaned[column] = cleaned[column].fillna("").astype(str).str.strip()

    title_columns = ["residence_hall", "category", "subcategory", "priority", "status", "assigned_team", "source", "resident_type", "reopened"]
    for column in title_columns:
        cleaned[column] = cleaned[column].str.title()

    cleaned["category"] = cleaned["category"].replace({"": "Other"})
    cleaned["status"] = cleaned["status"].replace({"": "Open"})
    cleaned["request_id"] = cleaned["request_id"].str.upper()

    for column in ["submitted_at", "assigned_at", "first_response_at", "resolved_at"]:
        cleaned[column] = pd.to_datetime(cleaned[column], errors="coerce")
    for column in ["estimated_cost_usd", "satisfaction_score"]:
        cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")

    cleaned = cleaned.drop_duplicates(subset=["request_id"], keep="first").reset_index(drop=True)
    cleaned["assignment_hours"] = (cleaned["assigned_at"] - cleaned["submitted_at"]).dt.total_seconds() / 3600
    cleaned["first_response_hours"] = (cleaned["first_response_at"] - cleaned["assigned_at"]).dt.total_seconds() / 3600
    cleaned["resolution_hours"] = (cleaned["resolved_at"] - cleaned["first_response_at"]).dt.total_seconds() / 3600
    cleaned["sla_target_hours"] = cleaned["priority"].map(SLA_TARGETS).fillna(SLA_TARGETS["Medium"])
    cleaned["within_assignment_sla"] = np.where(
        cleaned["status"].eq("Resolved") | cleaned["status"].eq("Open"),
        cleaned["assignment_hours"] <= cleaned["sla_target_hours"],
        np.nan,
    )
    cleaned["submitted_month"] = cleaned["submitted_at"].dt.to_period("M").astype(str)
    cleaned["submitted_weekday"] = cleaned["submitted_at"].dt.day_name()
    return cleaned


def summarize(cleaned: pd.DataFrame) -> tuple[dict[str, object], dict[str, pd.DataFrame]]:
    resolved = cleaned[cleaned["status"].eq("Resolved")]
    sla_population = cleaned[cleaned["status"].isin(["Resolved", "Open"])]
    metrics: dict[str, object] = {
        "raw_records": int(len(pd.read_csv(RAW_PATH))),
        "clean_records": int(len(cleaned)),
        "duplicate_records_removed": int(len(pd.read_csv(RAW_PATH)) - len(cleaned)),
        "total_requests": int(len(cleaned)),
        "resolved_requests": int(len(resolved)),
        "open_requests": int(cleaned["status"].eq("Open").sum()),
        "cancelled_requests": int(cleaned["status"].eq("Cancelled").sum()),
        "avg_assignment_hours": round(float(cleaned["assignment_hours"].mean()), 2),
        "median_assignment_hours": round(float(cleaned["assignment_hours"].median()), 2),
        "assignment_sla_rate": round(float(sla_population["within_assignment_sla"].mean() * 100), 1),
        "avg_resolution_hours": round(float(resolved["resolution_hours"].mean()), 2),
        "reopen_rate": round(float((resolved["reopened"].eq("Yes")).mean() * 100), 1),
        "avg_satisfaction": round(float(resolved["satisfaction_score"].mean()), 2),
        "total_estimated_cost_usd": round(float(cleaned["estimated_cost_usd"].sum()), 2),
    }

    category_summary = (
        cleaned.groupby("category", as_index=False)
        .agg(
            requests=("request_id", "count"),
            avg_assignment_hours=("assignment_hours", "mean"),
            assignment_sla_rate=("within_assignment_sla", "mean"),
            avg_resolution_hours=("resolution_hours", "mean"),
            reopen_rate=("reopened", lambda values: (values.eq("Yes")).mean()),
            estimated_cost_usd=("estimated_cost_usd", "sum"),
        )
        .sort_values("requests", ascending=False)
    )
    category_summary["assignment_sla_rate"] = category_summary["assignment_sla_rate"] * 100
    category_summary["reopen_rate"] = category_summary["reopen_rate"] * 100

    hall_summary = (
        cleaned.groupby("residence_hall", as_index=False)
        .agg(
            requests=("request_id", "count"),
            avg_assignment_hours=("assignment_hours", "mean"),
            assignment_sla_rate=("within_assignment_sla", "mean"),
            avg_resolution_hours=("resolution_hours", "mean"),
            open_requests=("status", lambda values: (values.eq("Open")).sum()),
        )
        .sort_values("avg_assignment_hours", ascending=False)
    )
    hall_summary["assignment_sla_rate"] = hall_summary["assignment_sla_rate"] * 100

    monthly_trend = (
        cleaned.groupby("submitted_month", as_index=False)
        .agg(
            requests=("request_id", "count"),
            avg_assignment_hours=("assignment_hours", "mean"),
            assignment_sla_rate=("within_assignment_sla", "mean"),
            avg_resolution_hours=("resolution_hours", "mean"),
        )
        .sort_values("submitted_month")
    )
    monthly_trend["assignment_sla_rate"] = monthly_trend["assignment_sla_rate"] * 100

    priority_summary = (
        cleaned.groupby("priority", as_index=False)
        .agg(
            requests=("request_id", "count"),
            avg_assignment_hours=("assignment_hours", "mean"),
            assignment_sla_rate=("within_assignment_sla", "mean"),
            avg_resolution_hours=("resolution_hours", "mean"),
        )
    )
    priority_summary["assignment_sla_rate"] = priority_summary["assignment_sla_rate"] * 100

    team_summary = (
        cleaned.groupby("assigned_team", as_index=False)
        .agg(
            requests=("request_id", "count"),
            avg_assignment_hours=("assignment_hours", "mean"),
            assignment_sla_rate=("within_assignment_sla", "mean"),
            open_requests=("status", lambda values: (values.eq("Open")).sum()),
            estimated_cost_usd=("estimated_cost_usd", "sum"),
        )
        .sort_values("requests", ascending=False)
    )
    team_summary["assignment_sla_rate"] = team_summary["assignment_sla_rate"] * 100

    issue_summary = (
        cleaned.groupby(["category", "subcategory"], as_index=False)
        .agg(
            requests=("request_id", "count"),
            avg_assignment_hours=("assignment_hours", "mean"),
            avg_resolution_hours=("resolution_hours", "mean"),
        )
        .sort_values("requests", ascending=False)
    )

    tables = {
        "category_summary": category_summary,
        "hall_summary": hall_summary,
        "monthly_trend": monthly_trend,
        "priority_summary": priority_summary,
        "team_summary": team_summary,
        "issue_summary": issue_summary,
    }
    return metrics, tables


def _save_chart(path: Path) -> None:
    plt.tight_layout()
    plt.savefig(path, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close()


def create_charts(tables: dict[str, pd.DataFrame]) -> None:
    plt.rcParams.update({"font.family": "DejaVu Sans", "axes.titleweight": "bold", "axes.titlesize": 13})

    category = tables["category_summary"].sort_values("requests")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(category["category"], category["requests"], color=COLOR)
    ax.set_title("Maintenance demand is concentrated in a few categories")
    ax.set_xlabel("Requests")
    ax.grid(axis="x", alpha=0.18)
    ax.spines[["top", "right", "left"]].set_visible(False)
    _save_chart(FIGURES_DIR / "category_volume.png")

    monthly = tables["monthly_trend"]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(monthly["submitted_month"], monthly["requests"], marker="o", color=COLOR, linewidth=2.5)
    ax.set_title("Monthly request volume shows move-in and seasonal spikes")
    ax.set_xlabel("Month")
    ax.set_ylabel("Requests")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(axis="y", alpha=0.18)
    ax.spines[["top", "right"]].set_visible(False)
    _save_chart(FIGURES_DIR / "monthly_volume.png")

    hall = tables["hall_summary"].sort_values("avg_assignment_hours")
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.barh(hall["residence_hall"], hall["avg_assignment_hours"], color=ORANGE)
    ax.axvline(4, color=NAVY, linestyle="--", linewidth=1.3, label="High-priority target")
    ax.set_title("Assignment speed varies by residence hall")
    ax.set_xlabel("Average assignment time (hours)")
    ax.grid(axis="x", alpha=0.18)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.legend(frameon=False)
    for bar in bars:
        ax.text(bar.get_width() + 0.08, bar.get_y() + bar.get_height() / 2, f"{bar.get_width():.1f}h", va="center", fontsize=9)
    _save_chart(FIGURES_DIR / "hall_assignment_performance.png")

    priority_order = ["Emergency", "High", "Medium", "Low"]
    priority = tables["priority_summary"].set_index("priority").reindex(priority_order).reset_index()
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(priority["priority"], priority["assignment_sla_rate"], color=["#b91c1c", "#ea580c", "#ca8a04", "#2563eb"])
    ax.axhline(90, color=NAVY, linestyle="--", linewidth=1.3, label="90% reference")
    ax.set_title("SLA performance is weakest for medium and low priority work")
    ax.set_ylabel("Requests within assignment SLA (%)")
    ax.set_ylim(0, 100)
    ax.grid(axis="y", alpha=0.18)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False)
    _save_chart(FIGURES_DIR / "priority_sla.png")

    issues = tables["issue_summary"].head(10).sort_values("requests")
    labels = issues["category"] + " — " + issues["subcategory"]
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(labels, issues["requests"], color=GREEN)
    ax.set_title("Top recurring issue types for process prioritization")
    ax.set_xlabel("Requests")
    ax.grid(axis="x", alpha=0.18)
    ax.spines[["top", "right", "left"]].set_visible(False)
    _save_chart(FIGURES_DIR / "top_issue_types.png")


def create_excel_dashboard(cleaned: pd.DataFrame, metrics: dict[str, object], tables: dict[str, pd.DataFrame]) -> None:
    with pd.ExcelWriter(EXCEL_PATH, engine="xlsxwriter", datetime_format="yyyy-mm-dd hh:mm") as writer:
        workbook = writer.book
        title_format = workbook.add_format({"bold": True, "font_size": 18, "font_color": "#0F172A"})
        subtitle_format = workbook.add_format({"font_color": "#475569", "italic": True})
        metric_label = workbook.add_format({"bold": True, "font_color": "#334155", "bg_color": "#E2E8F0", "border": 1})
        metric_value = workbook.add_format({"bold": True, "font_size": 16, "font_color": "#1D4ED8", "bg_color": "#F8FAFC", "border": 1, "align": "center"})
        note_format = workbook.add_format({"text_wrap": True, "valign": "top", "font_color": "#475569"})

        summary = workbook.add_worksheet("Executive Summary")
        writer.sheets["Executive Summary"] = summary
        summary.hide_gridlines(2)
        summary.set_column("A:A", 28)
        summary.set_column("B:B", 18)
        summary.set_column("C:C", 4)
        summary.set_column("D:H", 18)
        summary.write("A1", "Residence Hall Maintenance Operations Dashboard", title_format)
        summary.write("A2", "Synthetic data | 3,199 cleaned records | Built for portfolio demonstration", subtitle_format)
        summary.write("A4", "Key performance indicators", title_format)
        metric_pairs = [
            ("Total requests", metrics["total_requests"]),
            ("Avg. assignment time (hours)", metrics["avg_assignment_hours"]),
            ("Assignment SLA rate", f"{metrics['assignment_sla_rate']}%"),
            ("Avg. resolution time (hours)", metrics["avg_resolution_hours"]),
            ("Reopen rate", f"{metrics['reopen_rate']}%"),
            ("Avg. satisfaction", metrics["avg_satisfaction"]),
        ]
        for row_number, (label, value) in enumerate(metric_pairs, start=4):
            summary.write(row_number, 0, label, metric_label)
            summary.write(row_number, 1, value, metric_value)
        summary.write("D4", "Recommended actions", title_format)
        recommendations = [
            "1. Route emergency and high-priority requests through a dedicated triage queue.",
            "2. Use hall-level workload monitoring to rebalance assignments before backlogs grow.",
            "3. Create recurring-work playbooks for plumbing, HVAC, and furniture requests.",
            "4. Track assignment SLA weekly and review reopened requests for root causes.",
        ]
        for row_number, recommendation in enumerate(recommendations, start=5):
            summary.write(row_number, 3, recommendation, note_format)
        summary.set_row(4, 32)
        summary.set_row(5, 32)
        summary.set_row(6, 32)
        summary.set_row(7, 32)
        summary.insert_image("D11", str(FIGURES_DIR / "category_volume.png"), {"x_scale": 0.65, "y_scale": 0.65})

        for name, table in tables.items():
            export = table.copy()
            export.to_excel(writer, sheet_name=name[:31], index=False)
            worksheet = writer.sheets[name[:31]]
            worksheet.freeze_panes(1, 0)
            worksheet.autofilter(0, 0, len(export), len(export.columns) - 1)
            worksheet.set_default_row(18)
            worksheet.set_column(0, len(export.columns) - 1, 18)

        cleaned_export = cleaned.copy()
        for column in ["submitted_at", "assigned_at", "first_response_at", "resolved_at"]:
            cleaned_export[column] = cleaned_export[column].dt.strftime("%Y-%m-%d %H:%M:%S")
        cleaned_export.to_excel(writer, sheet_name="Cleaned Data", index=False)
        cleaned_sheet = writer.sheets["Cleaned Data"]
        cleaned_sheet.freeze_panes(1, 0)
        cleaned_sheet.autofilter(0, 0, len(cleaned_export), len(cleaned_export.columns) - 1)
        cleaned_sheet.set_default_row(18)
        cleaned_sheet.set_column(0, len(cleaned_export.columns) - 1, 16)


def write_report(metrics: dict[str, object], tables: dict[str, pd.DataFrame]) -> None:
    for name, table in tables.items():
        table.to_csv(TABLES_DIR / f"{name}.csv", index=False)
    (REPORTS_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    top_category = str(tables["category_summary"].iloc[0]["category"])
    top_category_count = int(tables["category_summary"].iloc[0]["requests"])
    slowest_hall = str(tables["hall_summary"].iloc[0]["residence_hall"])
    slowest_hall_hours = float(tables["hall_summary"].iloc[0]["avg_assignment_hours"])
    top_issue = tables["issue_summary"].iloc[0]
    top_issue_text = f"{top_issue['category']} — {top_issue['subcategory']} ({int(top_issue['requests'])} requests)"
    improvement = (1 - 2 / float(metrics["avg_assignment_hours"])) * 100

    report = f"""# Analysis Summary

## Project question

How can a residence-life operations team use maintenance-request data to identify recurring demand, improve routing, and reduce the time residents wait for action?

## Dataset and method

- **Source:** Synthetic, fictionalized maintenance-request records generated for portfolio use.
- **Raw records:** {metrics['raw_records']:,}
- **Clean records:** {metrics['clean_records']:,}
- **Quality check:** Removed {metrics['duplicate_records_removed']} duplicate request ID and standardized text/date fields.
- **Tools:** Python, pandas, NumPy, Matplotlib, SQL, and Excel.
- **Time period:** September 2025 through August 2026.

## Key findings

1. **Demand is concentrated:** {top_category} was the largest request category with {top_category_count:,} requests.
2. **Routing speed varies:** {slowest_hall} had the slowest average assignment time at {slowest_hall_hours:.1f} hours, signaling an opportunity for workload balancing or clearer ownership.
3. **Recurring work is visible:** The most common issue type was {top_issue_text}.
4. **SLA performance is measurable:** {metrics['assignment_sla_rate']}% of resolved/open requests met the priority-based assignment target.
5. **Resident experience is connected to speed:** Average satisfaction was {metrics['avg_satisfaction']}/5, while the reopen rate was {metrics['reopen_rate']}%.

## Recommended process improvements

1. Create an emergency/high-priority triage queue with an owner and escalation timer.
2. Review hall-level workload and open-request counts at a weekly operations huddle.
3. Build playbooks for high-volume categories such as plumbing, HVAC, and furniture.
4. Add a required category/subcategory field and automated duplicate-request check to the intake form.
5. Use a weekly SLA scorecard to identify slow routing before it becomes a resident-experience issue.

## Scenario analysis

If the team reduced average assignment time from {metrics['avg_assignment_hours']:.1f} hours to a **2-hour target**, the modeled improvement would be approximately **{improvement:.1f}%**. This is a planning scenario—not a measured result—and should be validated with operational data after implementation.

## Limitations

This repository uses synthetic data. The findings demonstrate the analysis workflow and should not be presented as official NJIT performance results. A real implementation would validate the definitions, SLA targets, cost fields, and privacy controls with the appropriate operations team.
"""
    (REPORTS_DIR / "analysis_summary.md").write_text(report, encoding="utf-8")


def main() -> None:
    _ensure_directories()
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"Raw dataset not found: {RAW_PATH}. Run src/generate_data.py first.")
    raw = pd.read_csv(RAW_PATH)
    cleaned = clean_data(raw)
    cleaned.to_csv(PROCESSED_PATH, index=False, date_format="%Y-%m-%d %H:%M:%S")
    metrics, tables = summarize(cleaned)
    create_charts(tables)
    create_excel_dashboard(cleaned, metrics, tables)
    write_report(metrics, tables)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
