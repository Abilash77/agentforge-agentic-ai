"""
AgentForge Project Dashboard Page.

Real-time agent progress tracking and file viewer.
"""

import json
import time
from typing import Optional

import requests
import streamlit as st

from agentforge.frontend.styles import inject_styles

API_BASE = "http://localhost:8001"

AGENT_INFO = {
    "product_manager":    {"icon": "👩‍💼", "name": "Product Manager",   "color": "#63b3ed"},
    "solution_architect": {"icon": "🏗️",  "name": "Solution Architect", "color": "#9f7aea"},
    "developer":          {"icon": "💻",  "name": "Developer",           "color": "#68d391"},
    "qa_engineer":        {"icon": "🧪",  "name": "QA Engineer",         "color": "#f6ad55"},
    "documentation":      {"icon": "📝",  "name": "Documentation",       "color": "#63b3ed"},
    "devops":             {"icon": "🐳",  "name": "DevOps",              "color": "#fc8181"},
    "ppt":                {"icon": "📊",  "name": "Presentations",       "color": "#9f7aea"},
}

# Expected % completion for each agent stage
AGENT_PROGRESS_MAP = {
    "product_manager": (0, 14),
    "solution_architect": (14, 28),
    "developer": (28, 50),
    "qa_engineer": (50, 65),
    "documentation": (50, 65),
    "ppt": (50, 65),
    "devops": (65, 90),
}

LANGUAGE_EXT = {
    "python": "python", "javascript": "javascript", "typescript": "typescript",
    "yaml": "yaml", "json": "json", "sql": "sql", "bash": "bash",
    "markdown": "markdown", "dockerfile": "dockerfile",
}


def _get_project(project_id: str) -> Optional[dict]:
    try:
        r = requests.get(f"{API_BASE}/api/v1/projects/{project_id}", timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def _get_files(project_id: str) -> list:
    try:
        r = requests.get(f"{API_BASE}/api/v1/projects/{project_id}/files", timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []


def _get_file_content(project_id: str, filename: str) -> Optional[str]:
    try:
        r = requests.get(
            f"{API_BASE}/api/v1/projects/{project_id}/files/{filename}",
            timeout=10,
        )
        if r.status_code == 200:
            return r.json().get("content", "")
    except Exception:
        pass
    return None


def show():
    inject_styles()

    st.markdown('<div class="section-header">📊 Project Dashboard</div>', unsafe_allow_html=True)

    # Project selector
    project_id = st.session_state.get("active_project_id", "")
    col1, col2 = st.columns([3, 1])
    with col1:
        project_id_input = st.text_input(
            "Project ID",
            value=project_id,
            placeholder="Enter project ID or select from History",
        )
    with col2:
        auto_refresh = st.checkbox("🔄 Auto-refresh", value=True)

    if project_id_input:
        project_id = project_id_input.strip()
        st.session_state["active_project_id"] = project_id

    if not project_id:
        st.info("👆 Enter a Project ID above or launch a new project from the **Home** page.")
        return

    # ── Fetch Project Data ────────────────────────────────────────────────────
    project = _get_project(project_id)
    if not project:
        st.error(f"Project `{project_id}` not found. Check the ID or API connection.")
        return

    # ── Project Header ────────────────────────────────────────────────────────
    status = project.get("status", "unknown")
    status_colors = {
        "pending": "#a0aec0", "in_progress": "#63b3ed",
        "agent_running": "#63b3ed", "completed": "#68d391", "failed": "#fc8181",
    }
    color = status_colors.get(status, "#a0aec0")

    st.markdown(
        f"""
        <div class="af-card">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <div style="font-size:1.4rem;font-weight:800;">{project.get('name','')}</div>
                    <div style="color:#718096;font-size:0.85rem;margin-top:0.3rem;">
                        ID: <code>{project_id[:16]}...</code> &nbsp;|&nbsp;
                        {project.get('project_type','')} &nbsp;|&nbsp; {project.get('tech_stack','')}
                    </div>
                </div>
                <div style="text-align:right;">
                    <span class="badge badge-{status}">{status.replace('_',' ').title()}</span>
                    <div style="margin-top:0.5rem;color:{color};font-size:1.8rem;font-weight:800;">
                        {project.get('progress_pct', 0)}%
                    </div>
                </div>
            </div>
            <div style="margin-top:1rem;">
                <div style="font-size:0.8rem;color:#718096;margin-bottom:0.3rem;">Overall Progress</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(project.get("progress_pct", 0) / 100)

    # ── Quick Metrics ─────────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(
            f'<div class="metric-card"><div class="metric-value">'
            f'{project.get("total_tokens",0):,}</div>'
            f'<div class="metric-label">Tokens Used</div></div>',
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            f'<div class="metric-card"><div class="metric-value">'
            f'${project.get("total_cost_usd",0):.3f}</div>'
            f'<div class="metric-label">Cost (USD)</div></div>',
            unsafe_allow_html=True,
        )
    with m3:
        files = _get_files(project_id)
        st.markdown(
            f'<div class="metric-card"><div class="metric-value">'
            f'{len(files)}</div>'
            f'<div class="metric-label">Files Generated</div></div>',
            unsafe_allow_html=True,
        )
    with m4:
        agent_runs = project.get("agent_runs", [])
        completed = sum(1 for r in agent_runs if r.get("status") == "completed")
        st.markdown(
            f'<div class="metric-card"><div class="metric-value">'
            f'{completed}/{len(AGENT_INFO)}</div>'
            f'<div class="metric-label">Agents Done</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Tabs: Progress | Files | Agent Runs ──────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs(["🤖 Agent Progress", "📁 Generated Files", "📋 Agent Runs", "⬇️ Download"])

    # Tab 1 — Agent Progress
    with tab1:
        current_agent = project.get("current_agent", "")
        completed_agents = {r.get("agent_role") for r in agent_runs if r.get("status") == "completed"}

        for role, info in AGENT_INFO.items():
            is_running = role == current_agent
            is_done = role in completed_agents
            card_class = "running" if is_running else ("completed" if is_done else "")
            icon = info["icon"]
            name = info["name"]
            color = info["color"]
            pct_range = AGENT_PROGRESS_MAP.get(role, (0, 100))
            overall_pct = project.get("progress_pct", 0)
            if is_done:
                agent_pct = 100
            elif is_running:
                rng = pct_range[1] - pct_range[0]
                within = max(0, overall_pct - pct_range[0])
                agent_pct = min(100, int((within / max(rng, 1)) * 100)) if rng > 0 else 50
            else:
                agent_pct = 0

            status_txt = "✓ Complete" if is_done else ("⚡ Running..." if is_running else "⏳ Waiting")

            st.markdown(
                f"""
                <div class="agent-card {card_class}">
                    <div style="display:flex;align-items:center;justify-content:space-between;">
                        <div style="display:flex;align-items:center;gap:0.7rem;">
                            <span style="font-size:1.5rem;">{icon}</span>
                            <div>
                                <div style="font-weight:700;color:{color};">{name}</div>
                                <div style="font-size:0.75rem;color:#718096;">{status_txt}</div>
                            </div>
                        </div>
                        <div style="font-size:1.2rem;font-weight:800;color:{color};">{agent_pct}%</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.progress(agent_pct / 100)

    # Tab 2 — Generated Files
    with tab2:
        if not files:
            st.info("No files generated yet. Launch the pipeline from the Home page.")
        else:
            # Group by agent role
            by_agent: dict = {}
            for f in files:
                r = f.get("agent_role", "misc")
                by_agent.setdefault(r, []).append(f)

            selected_file = st.selectbox(
                "Select file to view",
                [f["filename"] for f in files],
            )

            if selected_file:
                content = _get_file_content(project_id, selected_file)
                file_meta = next((f for f in files if f["filename"] == selected_file), {})
                lang = file_meta.get("language") or "text"
                ext_lang = LANGUAGE_EXT.get(lang, "")

                st.markdown(
                    f'<div style="font-size:0.8rem;color:#718096;margin-bottom:0.5rem;">'
                    f'📄 {selected_file} &nbsp;|&nbsp; {file_meta.get("size_bytes", 0):,} bytes &nbsp;|&nbsp; {lang}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                if content:
                    if ext_lang:
                        st.code(content, language=ext_lang)
                    else:
                        st.text_area("Content", content, height=500)

    # Tab 3 — Agent Runs
    with tab3:
        if not agent_runs:
            st.info("No agent runs recorded yet.")
        else:
            for run in sorted(agent_runs, key=lambda r: r.get("created_at", "")):
                role = run.get("agent_role", "")
                info = AGENT_INFO.get(role, {"icon": "🤖", "name": role, "color": "#a0aec0"})
                run_status = run.get("status", "")
                st.markdown(
                    f"""
                    <div class="af-card" style="margin-bottom:0.5rem;padding:0.8rem 1rem;">
                        <div style="display:flex;align-items:center;justify-content:space-between;">
                            <div>
                                <span style="color:{info['color']}">{info['icon']} {info['name']}</span>
                                &nbsp;→&nbsp; <code style="font-size:0.8rem;">{run.get('action_name','')}</code>
                            </div>
                            <div style="text-align:right;font-size:0.8rem;color:#718096;">
                                <span class="badge badge-{run_status}">{run_status}</span>
                                &nbsp; {run.get('total_tokens') or 0:,} tokens &nbsp;
                                ${run.get('cost_usd') or 0:.4f} &nbsp;
                                {run.get('duration_ms') or 0:,}ms
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # Tab 4 — Download
    with tab4:
        st.markdown("### ⬇️ Download Generated Files")
        if status == "completed":
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("📦 Download Full ZIP Package", use_container_width=True, type="primary"):
                    try:
                        r = requests.get(f"{API_BASE}/api/v1/projects/{project_id}/download", timeout=60)
                        if r.status_code == 200:
                            st.download_button(
                                "⬇️ Save ZIP",
                                data=r.content,
                                file_name=f"agentforge_{project_id[:8]}.zip",
                                mime="application/zip",
                            )
                        else:
                            st.error("Failed to generate download")
                    except Exception as e:
                        st.error(f"Download error: {e}")
        else:
            st.info(f"⏳ Download will be available when the project is **completed**. Current status: **{status}**")

    # ── Auto Refresh ──────────────────────────────────────────────────────────
    if auto_refresh and status in ("in_progress", "agent_running", "pending"):
        time.sleep(3)
        st.rerun()
