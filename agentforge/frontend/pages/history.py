"""AgentForge History Page"""
import requests
import streamlit as st
from agentforge.frontend.styles import inject_styles

API_BASE = "http://localhost:8001"


def show():
    inject_styles()
    st.markdown('<div class="section-header">📜 Project History</div>', unsafe_allow_html=True)

    try:
        r = requests.get(f"{API_BASE}/api/v1/projects?page=1&page_size=50", timeout=5)
        if r.status_code != 200:
            st.error("Could not fetch project history from API.")
            return
        data = r.json()
        projects = data.get("items", [])
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to AgentForge API. Make sure it's running on port 8001.")
        return

    if not projects:
        st.info("No projects yet. Launch your first project from the **Home** page!")
        return

    # Summary metrics
    total = data.get("total", 0)
    completed = sum(1 for p in projects if p["status"] == "completed")
    in_progress = sum(1 for p in projects if p["status"] in ("in_progress", "agent_running"))
    total_cost = sum(p.get("total_cost_usd", 0) for p in projects)
    total_tokens = sum(p.get("total_tokens", 0) for p in projects)

    m1, m2, m3, m4, m5 = st.columns(5)
    for col, val, lbl in [
        (m1, str(total), "Total Projects"),
        (m2, str(completed), "Completed"),
        (m3, str(in_progress), "In Progress"),
        (m4, f"${total_cost:.2f}", "Total Cost"),
        (m5, f"{total_tokens:,}", "Total Tokens"),
    ]:
        with col:
            st.markdown(
                f'<div class="metric-card"><div class="metric-value">{val}</div>'
                f'<div class="metric-label">{lbl}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # Search / filter
    search = st.text_input("🔍 Search projects", placeholder="Filter by name or idea...")

    for p in projects:
        if search and search.lower() not in p["name"].lower() and search.lower() not in p["idea"].lower():
            continue

        status = p.get("status", "unknown")
        with st.expander(f"{p['name']}  —  {status.replace('_',' ').title()}", expanded=False):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**Idea:** {p['idea'][:200]}{'...' if len(p['idea'])>200 else ''}")
                st.markdown(f"**Stack:** `{p['tech_stack']}` | **Type:** `{p['project_type']}`")
                st.markdown(f"**Created:** {p['created_at'][:19]}")
            with col2:
                st.metric("Tokens", f"{p.get('total_tokens',0):,}")
                st.metric("Cost", f"${p.get('total_cost_usd',0):.3f}")
            with col3:
                st.metric("Progress", f"{p.get('progress_pct',0)}%")
                if st.button("📊 View", key=f"view_{p['id']}"):
                    st.session_state["active_project_id"] = p["id"]
                    st.info("Switch to **Project Dashboard** tab to view this project.")
