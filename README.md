# Cosmos Ops Assistant

An AI-powered incident triage and operations dashboard for distributed database platforms (Azure SQL DB, Cosmos DB, PostgreSQL OSS).

Built to demonstrate hands-on experience with LLM APIs, database operations, incident management, and capacity planning — core competencies for platform PM roles on Azure Data teams.

## What it does

**Tab 1 — Incident Triage (LLM)**
- Paste any raw incident alert, error log, or symptom description
- OpenAI API classifies severity (P0/P1/P2), identifies database type, hypothesizes root cause, and drafts stakeholder comms
- Supports relational, non-relational, and OSS database failure scenarios

**Tab 2 — Incident Analytics (SQL + Data viz)**
- SQLite-backed incident log with 30 seeded historical incidents
- Charts: incidents by DB type, severity distribution, MTTR trends by week
- Root cause frequency table

**Tab 3 — Capacity Health (Supply chain)**
- Fleet-wide utilization snapshot (storage, CPU, connections, IOPS)
- Threshold-based alerting (Critical ≥85%, Warning ≥70%)
- 90-day storage utilization trend with threshold overlays

## Setup

1. Install dependencies:
```bash
pip install streamlit openai pandas plotly
```

2. Seed the incident database:
```bash
python seed_db.py
```

3. Run the app:
```bash
streamlit run app.py
```

4. Add your OpenAI API key in the sidebar (key stays local, never stored)

## Stack
- Python 3.8+
- OpenAI API (gpt-4o-mini)
- SQLite
- Streamlit
- Plotly

## Resume line
> Built an AI-powered incident triage and ops dashboard for a simulated distributed database platform; integrated OpenAI API for automated severity classification and root cause analysis across relational, non-relational, and OSS database failure scenarios; layered SQL-backed incident analytics and capacity utilization tracking to mirror real-world DRI workflows.
