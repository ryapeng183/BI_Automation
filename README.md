# BI Automation — Report Operations Automation

## 📌 Overview

This project automates **Power BI report operations and governance monitoring**, focusing on improving visibility, reliability, and ownership of reporting assets.

The goal is to reduce manual tracking and enable a **centralized, data-driven view of report health, usage, and risk** across workspaces.

This project is developed as part of a broader **Data Governance and BI Automation initiative**, with future expansion into KPI snapshotting and trend analysis.

---

## 🎯 Objective

Transform report operations from **manual, reactive tracking** into a **structured, automated system** that:

- Identifies failing and stale reports  
- Tracks ownership and governance gaps  
- Monitors refresh performance and reliability  
- Provides actionable insights for reporting health  

---

## 🧑‍💼 Target Users

- **Report Owners** → monitor refresh status and report usage  
- **Data Governance / BI Teams** → ensure ownership, compliance, and quality  
- **Workspace Admins** → manage report lifecycle and cleanup  
- **Leadership** → understand reporting reliability and adoption  

---

## ✅ Scope (v1)

This version focuses on **Report Operations Automation only**.

### In Scope
- Report inventory automation  
- Dataset (semantic model) inventory  
- Refresh monitoring and failure tracking  
- Usage tracking (high-level)  
- Ownership and governance signals  
- Stale and orphaned report detection  

### Out of Scope (for v1)
- KPI snapshotting and historical KPI tracking  
- Advanced predictive analytics on report usage  
- Full semantic lineage modeling  
- Real-time alert orchestration (basic logging only for now)  

---

## 🧱 Core Entities & Output Grain

All outputs follow a **clear, consistent grain** to ensure accurate joins and scalable reporting.

| Table | Grain | Description |
|------|------|-------------|
| `dim_workspace` | 1 row per workspace | Workspace metadata and ownership |
| `dim_report` | 1 row per report | Report inventory and governance attributes |
| `dim_dataset` | 1 row per dataset | Semantic model metadata and configuration |
| `fact_refresh_event` | 1 row per refresh attempt | Dataset refresh history and status |
| `fact_report_usage_day` | 1 row per report per day | Report usage and engagement signals |

---

## 🏗️ Architecture Overview

The project follows a standard **Extract → Transform → Load (ETL)** pipeline:

### 1. Extract
- Power BI Admin / REST APIs  
- Usage and activity logs  
- Metadata sources (reports, datasets, workspaces)  

### 2. Transform
- Normalize data into consistent grain  
- Create governance flags:
  - stale reports  
  - orphaned reports  
  - failed refreshes  
  - inactive assets  
- Ensure join-safe structures (avoid duplication)  

### 3. Load
- Store outputs in a structured data layer (e.g., SQL / governed storage)  
- Feed into Power BI dashboard for monitoring  

---

## 📊 Example Output Schema

### `dim_report`
``sql
report_id
report_name
workspace_id
owner
created_date
endorsement_status
is_stale_flag
is_orphan_flag
``

### `fact_refresh_event`
``sql
refresh_event_id
dataset_id
refresh_start_ts
refresh_end_ts
status
duration_seconds
error_code
``

### `fact_report_usage_day`
``sql
usage_date
report_id
view_count
unique_users
``

## 🚨 Key Governance Signals

This project produces actionable flags:

- ✅ **Stale Report** → no recent usage  
- ✅ **Orphan Report** → missing or invalid owner  
- ✅ **Failed Refresh** → recent failures detected  
- ✅ **Inactive Workspace** → low or no activity  
- ✅ **Uncertified Assets** → lacks endorsement / governance  

---

## 📈 Success Metrics

The project is successful when it can measure and improve:

- % of reports with assigned owners  
- % of datasets refreshing successfully  
- # of stale reports identified  
- # of orphaned assets detected  
- Reduction in manual tracking effort  
- Increased visibility into report health  

---

## ⚙️ Repository Structure (Suggested)

``
BI_Automation/
│
├── README.md
├── docs/
│   ├── architecture.md
│   ├── data_dictionary.md
│   
│
├── src/
│   ├── __init__.py/
│   ├── alerts.py/
│   ├── api_client.py/
│   ├── auth.py/
│   ├── delta_ops.py/
│   ├── discovery.py/
│   └── transform.py/
│
├── config/
│   ├── datasets.json/
│   ├── pipeline_config.json/
│   └── workflow.json/
│
├── output_samples/
└── tests/
    ├── local_auth_test.py/
    ├── rate_limit_probe.py/
    ├── test_dataset_refresh.py/
    └── test__report_query.py/

``

---

## ▶️ How It Works

1. Extract metadata and activity data from Power BI sources  
2. Transform into structured tables with consistent grain  
3. Generate governance signals (flags)  
4. Load into dataset for reporting and monitoring  
5. Visualize in Power BI dashboard  

---

## 🛠️ Operational Considerations

- **Scheduling**: Batch execution (daily recommended)  

- **Error Handling**:
  - Log failed extractions  
  - Capture refresh failures  

- **Data Quality Checks**:
  - Duplicate row checks  
  - Null owner validation  
  - Refresh-log consistency  

- **Security**:
  - Service principal authentication (recommended)  
  - Controlled access to output datasets  

---

## 🔮 Future Roadmap

### Phase 2 — KPI Snapshotting
- Historical KPI tracking  
- Trend analysis at defined grain  
- KPI prioritization framework  

### Phase 3 — Advanced Governance
- Report prioritization scoring  
- Adoption and engagement modeling  
- Predictive failure detection  

---

## ⚠️ Key Assumptions

- Each report belongs to a single workspace  
- Dataset refresh is the primary reliability signal  
- Daily aggregation is sufficient for usage tracking (v1)  
- Ownership metadata is available or can be derived  

---

## 🚀 Next Steps

- Finalize data source connections (APIs / logs)  
- Build core dimension + fact tables  
- Validate row counts and grain consistency  
- Develop monitoring dashboard  
- Iterate on governance signals  

---

## 🤝 Contribution

This is an evolving internal project. Contributions may include:

- Improving data models  
- Refining governance rules  
- Adding automation workflows  
- Expanding reporting capabilities  

---

## 🧠 Summary

This project establishes the **foundation for BI governance automation** by:

- Standardizing report metadata  
- Structuring operational signals  
- Enabling scalable monitoring  

It is designed to be **extensible**, with future layers (KPI tracking, analytics, and optimization) built on top of a strong operational core.
