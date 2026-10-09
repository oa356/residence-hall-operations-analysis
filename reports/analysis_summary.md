# Analysis Summary

## Project question

How can a residence-life operations team use maintenance-request data to identify recurring demand, improve routing, and reduce the time residents wait for action?

## Dataset and method

- **Source:** Synthetic, fictionalized maintenance-request records generated for portfolio use.
- **Raw records:** 3,200
- **Clean records:** 3,199
- **Quality check:** Removed 1 duplicate request ID and standardized text/date fields.
- **Tools:** Python, pandas, NumPy, Matplotlib, SQL, and Excel.
- **Time period:** September 2025 through August 2026.

## Key findings

1. **Demand is concentrated:** Plumbing was the largest request category with 676 requests.
2. **Routing speed varies:** Talbott Hall had the slowest average assignment time at 5.8 hours, signaling an opportunity for workload balancing or clearer ownership.
3. **Recurring work is visible:** The most common issue type was Plumbing — Toilet (173 requests).
4. **SLA performance is measurable:** 87.0% of resolved/open requests met the priority-based assignment target.
5. **Resident experience is connected to speed:** Average satisfaction was 4.24/5, while the reopen rate was 9.8%.

## Recommended process improvements

1. Create an emergency/high-priority triage queue with an owner and escalation timer.
2. Review hall-level workload and open-request counts at a weekly operations huddle.
3. Build playbooks for high-volume categories such as plumbing, HVAC, and furniture.
4. Add a required category/subcategory field and automated duplicate-request check to the intake form.
5. Use a weekly SLA scorecard to identify slow routing before it becomes a resident-experience issue.

## Scenario analysis

If the team reduced average assignment time from 5.6 hours to a **2-hour target**, the modeled improvement would be approximately **64.2%**. This is a planning scenario—not a measured result—and should be validated with operational data after implementation.

## Limitations

This repository uses synthetic data. The findings demonstrate the analysis workflow and should not be presented as official NJIT performance results. A real implementation would validate the definitions, SLA targets, cost fields, and privacy controls with the appropriate operations team.
