import streamlit as st
import openai
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import random

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Cosmos Ops Assistant",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .main { background-color: #0f1117; }

    .metric-card {
        background: linear-gradient(135deg, #1a1f2e 0%, #16213e 100%);
        border: 1px solid #2d3748;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    }
    .metric-number { font-size: 2rem; font-weight: 700; color: #00d4ff; }
    .metric-label { font-size: 0.8rem; color: #8892a4; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px; }

    .severity-P0 { background: #2d1515; border-left: 4px solid #ff4444; padding: 12px 16px; border-radius: 6px; margin: 8px 0; }
    .severity-P1 { background: #2d2015; border-left: 4px solid #ff8800; padding: 12px 16px; border-radius: 6px; margin: 8px 0; }
    .severity-P2 { background: #1a2d15; border-left: 4px solid #44ff88; padding: 12px 16px; border-radius: 6px; margin: 8px 0; }

    .triage-output {
        background: #1a1f2e;
        border: 1px solid #2d3748;
        border-radius: 10px;
        padding: 24px;
        margin-top: 16px;
    }
    .triage-section { margin-bottom: 16px; }
    .triage-label { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 2px; color: #8892a4; margin-bottom: 4px; }
    .triage-value { font-size: 1rem; color: #e2e8f0; }

    .capacity-bar-container { margin: 8px 0; }
    .capacity-label { font-size: 0.85rem; color: #8892a4; margin-bottom: 4px; }

    .stTextArea textarea { font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; background: #1a1f2e; color: #e2e8f0; border: 1px solid #2d3748; }
    .stButton > button { background: linear-gradient(135deg, #0066cc, #00d4ff); color: white; border: none; border-radius: 8px; padding: 10px 24px; font-weight: 600; font-size: 0.9rem; width: 100%; }
    .stButton > button:hover { opacity: 0.9; transform: translateY(-1px); }

    div[data-testid="stTab"] button { font-weight: 600; }
    .stTabs [data-baseweb="tab-list"] { background: #1a1f2e; border-radius: 8px; padding: 4px; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛢️ Cosmos Ops Assistant")
    st.markdown("*AI-powered incident triage for distributed database platforms*")
    st.divider()
    api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-proj-...")
    st.caption("Key stays local — never stored or sent anywhere except OpenAI.")
    st.divider()
    st.markdown("**Platform Coverage**")
    st.markdown("🔵 Azure SQL DB (Relational)")
    st.markdown("🟠 Cosmos DB (Non-relational)")
    st.markdown("🟢 PostgreSQL (OSS)")
    st.divider()
    st.markdown("**Built by:** Prapti Kille")
    st.markdown("**Stack:** Python · OpenAI API · SQLite · Streamlit · Plotly")

# ── Auto-seed DB if missing (needed for cloud deployment) ────────────────────
import os
if not os.path.exists("incidents.db"):
    import seed_db  # importing the module runs it and seeds the database

# ── DB helper ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_incidents():
    conn = sqlite3.connect("incidents.db")
    df = pd.read_sql("SELECT * FROM incidents", conn)
    conn.close()
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["week"] = df["created_at"].dt.to_period("W").astype(str)
    return df

# ── LLM triage ────────────────────────────────────────────────────────────────
def run_triage(incident_text, api_key):
    client = openai.OpenAI(api_key=api_key)
    system_prompt = """You are a senior Site Reliability Engineer and DRI (Directly Responsible Individual) 
for a large-scale distributed database platform running Azure SQL DB, Cosmos DB, and PostgreSQL (OSS) workloads.

When given an incident report, respond ONLY in this exact JSON format:
{
  "severity": "P0 | P1 | P2",
  "db_type": "Azure SQL DB | Cosmos DB | PostgreSQL (OSS) | Unknown",
  "root_cause": "One sentence root cause hypothesis",
  "confidence": "High | Medium | Low",
  "immediate_actions": ["action 1", "action 2", "action 3"],
  "stakeholder_update": "A 2-3 sentence stakeholder communication draft, professional tone",
  "follow_up": "One sentence post-incident review recommendation"
}

Severity guide:
- P0: Customer-facing outage or data loss risk
- P1: Significant degradation, workaround exists
- P2: Minor issue, minimal customer impact

Respond ONLY with valid JSON. No preamble, no explanation."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Incident report:\n\n{incident_text}"}
        ],
        temperature=0.2,
        max_tokens=600
    )
    import json
    return json.loads(response.choices[0].message.content)

# ── Sample incidents ──────────────────────────────────────────────────────────
SAMPLE_INCIDENTS = {
    "Cosmos DB write timeout": """[ALERT] 14:32 UTC - Cosmos DB write latency p99 > 8000ms (threshold: 500ms)
Service: OrderProcessingService
Region: East US 2
Error: RequestRateTooLargeException on partition key /customerId
RU/s consumed: 98% of provisioned 10,000 RU/s
Affected customers: ~2,400 enterprise accounts
Error rate: 34% of write operations failing
Throughput: Dropped from 850 req/s to 180 req/s""",

    "Azure SQL deadlock spike": """[INCIDENT] Azure SQL DB - Deadlock spike detected
Database: prod-orders-db (Business Critical tier)
Time: 09:15 UTC
Deadlocks/min: 47 (baseline: 0.3)
Affected query: UPDATE inventory SET quantity = quantity - @qty WHERE product_id = @id
Sessions blocked: 312
CPU: 91% sustained for 18 minutes
App errors: "Transaction (Process ID 87) was deadlocked on lock resources" """,

    "PostgreSQL replication lag": """[WARNING] PostgreSQL OSS - Replication lag critical
Primary: pg-prod-01 (West Europe)
Replica: pg-prod-01-replica (North Europe)
Replication lag: 4m 32s (threshold: 30s)
WAL sender process: Running but slow
Network throughput between regions: 120 Mbps (expected: 800 Mbps)
Potential cause: Large batch job inserted 18M rows at 08:45 UTC
Read replicas currently serving stale data"""
}

# ── TABS ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🚨 Incident Triage", "📊 Incident Analytics", "⚡ Capacity Health"])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1: INCIDENT TRIAGE
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown("### AI-Powered Incident Triage")
    st.markdown("Paste a raw incident alert or log snippet. The assistant classifies severity, identifies root cause, and drafts stakeholder comms.")

    col1, col2 = st.columns([1.2, 1])

    with col1:
        st.markdown("**Load a sample incident**")
        sample_choice = st.selectbox("", ["— choose a sample —"] + list(SAMPLE_INCIDENTS.keys()), label_visibility="collapsed")

        if sample_choice != "— choose a sample —":
            default_text = SAMPLE_INCIDENTS[sample_choice]
        else:
            default_text = ""

        incident_input = st.text_area(
            "Incident report / alert payload",
            value=default_text,
            height=280,
            placeholder="Paste error logs, alert text, or incident description here..."
        )

        run_btn = st.button("Run Triage →", disabled=not api_key or not incident_input)
        if not api_key:
            st.caption("⚠️ Add your OpenAI API key in the sidebar to enable triage.")

    with col2:
        if run_btn and api_key and incident_input:
            with st.spinner("Analyzing incident..."):
                try:
                    result = run_triage(incident_input, api_key)

                    sev = result.get("severity", "P2")
                    sev_colors = {"P0": "#ff4444", "P1": "#ff8800", "P2": "#44ff88"}
                    sev_color = sev_colors.get(sev, "#8892a4")

                    st.markdown(f"""
                    <div class="triage-output">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
                            <span style="font-size:1.3rem; font-weight:700; color:#e2e8f0;">Triage Result</span>
                            <span style="background:{sev_color}22; color:{sev_color}; border:1px solid {sev_color}; border-radius:20px; padding:4px 14px; font-weight:700; font-size:0.9rem;">{sev}</span>
                        </div>
                        <div class="triage-section">
                            <div class="triage-label">Database Type</div>
                            <div class="triage-value">🗄️ {result.get('db_type', 'Unknown')}</div>
                        </div>
                        <div class="triage-section">
                            <div class="triage-label">Root Cause Hypothesis</div>
                            <div class="triage-value">🔍 {result.get('root_cause', '')}</div>
                        </div>
                        <div class="triage-section">
                            <div class="triage-label">Confidence</div>
                            <div class="triage-value">📊 {result.get('confidence', '')}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown("**Immediate Actions**")
                    for i, action in enumerate(result.get("immediate_actions", []), 1):
                        st.markdown(f"`{i}.` {action}")

                    st.markdown("**Stakeholder Update Draft**")
                    st.info(result.get("stakeholder_update", ""))

                    st.markdown("**Post-Incident Follow-up**")
                    st.success(result.get("follow_up", ""))

                except Exception as e:
                    st.error(f"Triage failed: {str(e)}")
        else:
            st.markdown("""
            <div style="background:#1a1f2e; border:1px dashed #2d3748; border-radius:10px; padding:40px; text-align:center; color:#8892a4; height:400px; display:flex; flex-direction:column; justify-content:center;">
                <div style="font-size:2rem; margin-bottom:12px;">🔍</div>
                <div style="font-weight:600; margin-bottom:8px; color:#e2e8f0;">Triage output appears here</div>
                <div style="font-size:0.85rem;">Load a sample incident or paste your own,<br>then click Run Triage</div>
            </div>
            """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2: INCIDENT ANALYTICS
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown("### Incident Log Analytics")
    st.markdown("90-day incident history across the Cosmos platform database fleet.")

    df = load_incidents()

    # KPI row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-number">{len(df)}</div><div class="metric-label">Total Incidents</div></div>', unsafe_allow_html=True)
    with c2:
        p0_count = len(df[df.severity == "P0"])
        st.markdown(f'<div class="metric-card"><div class="metric-number" style="color:#ff4444">{p0_count}</div><div class="metric-label">P0 Incidents</div></div>', unsafe_allow_html=True)
    with c3:
        avg_mttr = int(df.mttr_minutes.mean())
        st.markdown(f'<div class="metric-card"><div class="metric-number">{avg_mttr}m</div><div class="metric-label">Avg MTTR</div></div>', unsafe_allow_html=True)
    with c4:
        p0_mttr = int(df[df.severity == "P0"].mttr_minutes.mean()) if p0_count > 0 else 0
        st.markdown(f'<div class="metric-card"><div class="metric-number" style="color:#ff8800">{p0_mttr}m</div><div class="metric-label">P0 Avg MTTR</div></div>', unsafe_allow_html=True)

    st.markdown("")

    col1, col2 = st.columns(2)

    with col1:
        # Incidents by DB type
        db_counts = df.groupby("db_type").size().reset_index(name="count")
        fig1 = px.bar(db_counts, x="db_type", y="count",
                      color="db_type",
                      color_discrete_map={"Azure SQL DB": "#0066cc", "Cosmos DB": "#ff8800", "PostgreSQL (OSS)": "#44aa55"},
                      title="Incidents by Database Type",
                      labels={"db_type": "", "count": "Incidents"})
        fig1.update_layout(
            paper_bgcolor="#1a1f2e", plot_bgcolor="#1a1f2e",
            font_color="#8892a4", title_font_color="#e2e8f0",
            showlegend=False, margin=dict(t=40, b=20)
        )
        fig1.update_xaxes(tickfont=dict(color="#e2e8f0"))
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        # Severity breakdown
        sev_counts = df.groupby("severity").size().reset_index(name="count")
        fig2 = px.pie(sev_counts, values="count", names="severity",
                      color="severity",
                      color_discrete_map={"P0": "#ff4444", "P1": "#ff8800", "P2": "#44ff88"},
                      title="Severity Distribution",
                      hole=0.5)
        fig2.update_layout(
            paper_bgcolor="#1a1f2e", plot_bgcolor="#1a1f2e",
            font_color="#8892a4", title_font_color="#e2e8f0",
            margin=dict(t=40, b=20)
        )
        st.plotly_chart(fig2, use_container_width=True)

    # MTTR trend over time
    mttr_by_week = df.groupby(["week", "severity"])["mttr_minutes"].mean().reset_index()
    fig3 = px.line(mttr_by_week, x="week", y="mttr_minutes", color="severity",
                   color_discrete_map={"P0": "#ff4444", "P1": "#ff8800", "P2": "#44ff88"},
                   title="Mean Time to Resolve (MTTR) by Week",
                   labels={"mttr_minutes": "MTTR (minutes)", "week": ""})
    fig3.update_layout(
        paper_bgcolor="#1a1f2e", plot_bgcolor="#1a1f2e",
        font_color="#8892a4", title_font_color="#e2e8f0",
        margin=dict(t=40, b=20)
    )
    st.plotly_chart(fig3, use_container_width=True)

    # Root cause table
    st.markdown("**Most Frequent Root Causes**")
    rc_counts = df.groupby("root_cause").size().reset_index(name="occurrences").sort_values("occurrences", ascending=False)
    st.dataframe(rc_counts, use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3: CAPACITY HEALTH
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown("### Platform Capacity Health")
    st.markdown("Real-time utilization snapshot across the Cosmos database fleet. Flags resources approaching capacity thresholds.")

    # Mock capacity data
    resources = [
        {"name": "Azure SQL DB — East US 2", "type": "Relational", "storage_pct": 87, "cpu_pct": 72, "connections_pct": 61, "iops_pct": 78},
        {"name": "Azure SQL DB — West Europe", "type": "Relational", "storage_pct": 54, "cpu_pct": 45, "connections_pct": 38, "iops_pct": 42},
        {"name": "Cosmos DB — East US 2", "type": "Non-relational", "storage_pct": 63, "cpu_pct": 91, "connections_pct": 55, "iops_pct": 88},
        {"name": "Cosmos DB — Southeast Asia", "type": "Non-relational", "storage_pct": 41, "cpu_pct": 38, "connections_pct": 29, "iops_pct": 35},
        {"name": "PostgreSQL OSS — West US", "type": "OSS", "storage_pct": 95, "cpu_pct": 58, "connections_pct": 72, "iops_pct": 64},
        {"name": "PostgreSQL OSS — North Europe", "type": "OSS", "storage_pct": 48, "cpu_pct": 31, "connections_pct": 44, "iops_pct": 39},
    ]

    def pct_color(pct):
        if pct >= 85: return "#ff4444"
        if pct >= 70: return "#ff8800"
        return "#44ff88"

    def flag(pct):
        if pct >= 85: return "🔴 Critical"
        if pct >= 70: return "🟡 Warning"
        return "🟢 Healthy"

    # Summary flags
    critical = sum(1 for r in resources if any(r[k] >= 85 for k in ["storage_pct", "cpu_pct", "connections_pct", "iops_pct"]))
    warning = sum(1 for r in resources if any(70 <= r[k] < 85 for k in ["storage_pct", "cpu_pct", "connections_pct", "iops_pct"]) and not any(r[k] >= 85 for k in ["storage_pct", "cpu_pct", "connections_pct", "iops_pct"]))

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-number" style="color:#ff4444">{critical}</div><div class="metric-label">Critical Resources</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div class="metric-number" style="color:#ff8800">{warning}</div><div class="metric-label">Warning Resources</div></div>', unsafe_allow_html=True)
    with c3:
        healthy = len(resources) - critical - warning
        st.markdown(f'<div class="metric-card"><div class="metric-number" style="color:#44ff88">{healthy}</div><div class="metric-label">Healthy Resources</div></div>', unsafe_allow_html=True)

    st.markdown("")

    # Resource cards
    for r in resources:
        with st.expander(f"{'🔴' if any(r[k] >= 85 for k in ['storage_pct','cpu_pct','connections_pct','iops_pct']) else '🟡' if any(r[k] >= 70 for k in ['storage_pct','cpu_pct','connections_pct','iops_pct']) else '🟢'}  {r['name']}  —  {r['type']}"):
            col1, col2, col3, col4 = st.columns(4)
            metrics = [
                ("Storage", r["storage_pct"], col1),
                ("CPU", r["cpu_pct"], col2),
                ("Connections", r["connections_pct"], col3),
                ("IOPS", r["iops_pct"], col4),
            ]
            for label, pct, col in metrics:
                with col:
                    color = pct_color(pct)
                    st.markdown(f"""
                    <div style="text-align:center;">
                        <div style="font-size:0.7rem; color:#8892a4; text-transform:uppercase; letter-spacing:1px; margin-bottom:4px;">{label}</div>
                        <div style="font-size:1.8rem; font-weight:700; color:{color};">{pct}%</div>
                        <div style="font-size:0.75rem; color:{color};">{flag(pct)}</div>
                    </div>
                    """, unsafe_allow_html=True)

            # Capacity recommendation
            if any(r[k] >= 85 for k in ["storage_pct", "cpu_pct", "connections_pct", "iops_pct"]):
                bottleneck = max(["storage_pct", "cpu_pct", "connections_pct", "iops_pct"], key=lambda k: r[k]).replace("_pct", "").upper()
                st.error(f"⚠️ Capacity review required: {bottleneck} utilization critical. Recommend initiating supply chain request for additional capacity within 48 hours.")
            elif any(r[k] >= 70 for k in ["storage_pct", "cpu_pct", "connections_pct", "iops_pct"]):
                st.warning("📋 Monitor closely. Schedule capacity planning review for next sprint.")

    # Capacity trend chart
    st.markdown("**Fleet-Wide Storage Utilization Trend (90 days)**")
    import numpy as np
    days = pd.date_range(end=datetime.now(), periods=90, freq="D")
    np.random.seed(42)
    storage_trend = pd.DataFrame({
        "date": days,
        "Azure SQL DB": np.clip(60 + np.cumsum(np.random.randn(90) * 0.5), 40, 98),
        "Cosmos DB": np.clip(45 + np.cumsum(np.random.randn(90) * 0.4), 30, 98),
        "PostgreSQL OSS": np.clip(70 + np.cumsum(np.random.randn(90) * 0.6), 40, 99),
    })

    fig4 = go.Figure()
    colors = {"Azure SQL DB": "#0066cc", "Cosmos DB": "#ff8800", "PostgreSQL OSS": "#44aa55"}
    for col in ["Azure SQL DB", "Cosmos DB", "PostgreSQL OSS"]:
        fig4.add_trace(go.Scatter(x=storage_trend["date"], y=storage_trend[col],
                                   name=col, line=dict(color=colors[col], width=2)))
    fig4.add_hline(y=85, line_dash="dash", line_color="#ff4444", annotation_text="Critical threshold (85%)")
    fig4.add_hline(y=70, line_dash="dash", line_color="#ff8800", annotation_text="Warning threshold (70%)")
    fig4.update_layout(
        paper_bgcolor="#1a1f2e", plot_bgcolor="#1a1f2e",
        font_color="#8892a4", yaxis_title="Storage Utilization %",
        margin=dict(t=20, b=20), legend=dict(bgcolor="#1a1f2e")
    )
    st.plotly_chart(fig4, use_container_width=True)
