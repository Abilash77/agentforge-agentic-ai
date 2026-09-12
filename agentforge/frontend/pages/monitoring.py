"""AgentForge Monitoring Page"""
import requests
import streamlit as st

from agentforge.frontend.styles import inject_styles

API_BASE = "http://localhost:8001"


def show():
    inject_styles()
    st.markdown('<div class="section-header">📈 Monitoring & Analytics</div>', unsafe_allow_html=True)

    try:
        import plotly.graph_objects as go
        import plotly.express as px
        PLOTLY_AVAILABLE = True
    except ImportError:
        PLOTLY_AVAILABLE = False

    tab1, tab2, tab3 = st.tabs(["💰 Cost Analytics", "⚡ Agent Performance", "🌐 Platform Summary"])

    with tab1:
        st.markdown("### 💰 Cost Breakdown by Project")
        try:
            r = requests.get(f"{API_BASE}/api/v1/monitoring/costs?limit=30", timeout=5)
            costs = r.json() if r.status_code == 200 else []

            if costs and PLOTLY_AVAILABLE:
                names = [c["project_name"][:20] for c in costs]
                values = [c["total_cost_usd"] for c in costs]
                tokens = [c["total_tokens"] for c in costs]

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    name="Cost (USD)", x=names, y=values,
                    marker_color="#63b3ed", opacity=0.85,
                ))
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    font={"color": "#e2e8f0"}, xaxis={"gridcolor": "rgba(255,255,255,0.05)"},
                    yaxis={"gridcolor": "rgba(255,255,255,0.05)", "title": "Cost (USD)"},
                    showlegend=False, margin={"t": 10, "b": 30},
                )
                st.plotly_chart(fig, use_container_width=True)

                # Table
                st.dataframe(
                    [{"Project": c["project_name"], "Cost $": f"{c['total_cost_usd']:.4f}",
                      "Tokens": f"{c['total_tokens']:,}", "Status": c["status"]}
                     for c in costs],
                    use_container_width=True,
                )
            elif costs:
                st.json(costs)
            else:
                st.info("No cost data yet. Complete some projects first.")
        except Exception as e:
            st.error(f"Could not fetch cost data: {e}")

    with tab2:
        st.markdown("### ⚡ Agent Performance Metrics")
        try:
            r = requests.get(f"{API_BASE}/api/v1/monitoring/performance", timeout=5)
            perf = r.json() if r.status_code == 200 else {}
            agents = perf.get("agents", [])

            if agents and PLOTLY_AVAILABLE:
                roles = [a["agent_role"].replace("_", " ").title() for a in agents]
                avg_tokens = [a["avg_tokens"] for a in agents]
                avg_cost = [a["avg_cost_usd"] for a in agents]
                avg_ms = [a["avg_duration_ms"] / 1000 for a in agents]

                col1, col2 = st.columns(2)
                with col1:
                    fig = go.Figure(go.Bar(
                        x=roles, y=avg_tokens, marker_color="#9f7aea", opacity=0.85,
                    ))
                    fig.update_layout(
                        title="Avg Tokens per Agent",
                        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                        font={"color": "#e2e8f0"},
                        yaxis={"gridcolor": "rgba(255,255,255,0.05)"},
                        margin={"t": 40, "b": 30},
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    fig2 = go.Figure(go.Bar(
                        x=roles, y=avg_ms, marker_color="#68d391", opacity=0.85,
                    ))
                    fig2.update_layout(
                        title="Avg Duration (seconds)",
                        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                        font={"color": "#e2e8f0"},
                        yaxis={"gridcolor": "rgba(255,255,255,0.05)"},
                        margin={"t": 40, "b": 30},
                    )
                    st.plotly_chart(fig2, use_container_width=True)

                st.dataframe(agents, use_container_width=True)
            else:
                st.info("No performance data yet.")
        except Exception as e:
            st.error(f"Could not fetch performance data: {e}")

    with tab3:
        st.markdown("### 🌐 Platform Summary")
        try:
            r = requests.get(f"{API_BASE}/api/v1/monitoring/summary", timeout=5)
            if r.status_code == 200:
                summary = r.json()
                s1, s2, s3, s4 = st.columns(4)
                for col, val, lbl in [
                    (s1, str(summary.get("total_projects", 0)), "Total Projects"),
                    (s2, str(summary.get("completed_projects", 0)), "Completed"),
                    (s3, f"{summary.get('total_tokens_used', 0):,}", "Total Tokens"),
                    (s4, f"${summary.get('total_cost_usd', 0):.2f}", "Total Cost"),
                ]:
                    with col:
                        st.markdown(
                            f'<div class="metric-card"><div class="metric-value">{val}</div>'
                            f'<div class="metric-label">{lbl}</div></div>',
                            unsafe_allow_html=True,
                        )
        except Exception as e:
            st.error(f"Could not fetch platform summary: {e}")

        # Task Queue Status
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 📋 Task Queue Status")
        try:
            r = requests.get(f"{API_BASE}/api/v1/agents/status", timeout=5)
            if r.status_code == 200:
                status_data = r.json()
                c1, c2 = st.columns(2)
                with c1:
                    st.metric("Queue Size", status_data.get("queue_size", 0))
                with c2:
                    st.metric("Running", status_data.get("running_count", 0))
                tasks = status_data.get("tasks", [])
                if tasks:
                    st.dataframe(tasks, use_container_width=True)
        except Exception as e:
            st.error(f"Could not fetch task status: {e}")
