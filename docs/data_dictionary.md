# Data dictionary

| Field | Description |
| --- | --- |
| `request_id` | Synthetic maintenance-request identifier. |
| `submitted_at` | Timestamp when the request entered the queue. |
| `residence_hall` | Fictional building associated with the request. |
| `floor` | Floor number or common-area label. |
| `room_or_area` | Fictional room/area label; contains no resident identity. |
| `category` | Broad request category such as Plumbing, HVAC, or Access. |
| `subcategory` | More specific issue type. |
| `priority` | Emergency, High, Medium, or Low. |
| `status` | Resolved, Open, or Cancelled. |
| `assigned_team` | Fictional team responsible for the work. |
| `source` | Intake channel. |
| `resident_type` | Synthetic requestor type. |
| `assigned_at` | Timestamp when the request was routed to a team. |
| `first_response_at` | Timestamp of the first team response. |
| `resolved_at` | Timestamp when work was marked resolved. |
| `estimated_cost_usd` | Synthetic estimated service cost. |
| `satisfaction_score` | Synthetic 1–5 score for resolved requests. |
| `reopened` | Whether the request was reopened after resolution. |
| `assignment_hours` | Derived hours from submission to assignment. |
| `first_response_hours` | Derived hours from assignment to first response. |
| `resolution_hours` | Derived hours from first response to resolution. |
| `sla_target_hours` | Priority-based assignment target used in the analysis. |
| `within_assignment_sla` | Whether assignment occurred within the target. |
| `submitted_month` | Month derived from `submitted_at`. |
| `submitted_weekday` | Weekday derived from `submitted_at`. |
