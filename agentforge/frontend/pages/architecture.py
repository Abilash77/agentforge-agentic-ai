"""AgentForge Architecture Viewer Page"""
import re
import requests
import streamlit as st
from agentforge.frontend.styles import inject_styles

API_BASE = "http://localhost:8001"


def _render_mermaid(mermaid_code: str) -> None:
    """Render Mermaid diagram using the Mermaid JS CDN."""
    clean = mermaid_code.strip()
    html = f"""
    <div class="mermaid" style="background:transparent;">
{clean}
    </div>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>mermaid.initialize({{startOnLoad:true, theme:'dark'}});</script>
    """
    st.components.v1.html(html, height=500, scrolling=True)


def show():
    inject_styles()
    st.markdown('<div class="section-header">🏗️ Architecture Viewer</div>', unsafe_allow_html=True)

    project_id = st.session_state.get("active_project_id", "")
    project_id = st.text_input("Project ID", value=project_id, placeholder="Enter project ID")

    if not project_id:
        st.info("Enter a Project ID to view architecture artifacts.")
        return

    # Fetch generated files
    try:
        r = requests.get(f"{API_BASE}/api/v1/projects/{project_id}/files", timeout=5)
        files = r.json() if r.status_code == 200 else []
    except Exception:
        st.error("Cannot connect to API.")
        return

    arch_files = {f["filename"]: f for f in files if f["agent_role"] == "solution_architect"}

    if not arch_files:
        st.info("No architecture files generated yet for this project.")
        return

    tab1, tab2, tab3, tab4 = st.tabs([
        "🗺️ Architecture Diagrams", "📊 Database Schema", "🔌 API Spec", "💡 Tech Stack"
    ])

    def fetch_content(filename: str) -> str:
        try:
            r = requests.get(f"{API_BASE}/api/v1/projects/{project_id}/files/{filename}", timeout=10)
            return r.json().get("content", "") if r.status_code == 200 else ""
        except Exception:
            return ""

    with tab1:
        arch_file = arch_files.get("ARCHITECTURE.md")
        if arch_file:
            content = fetch_content("ARCHITECTURE.md")
            if content:
                # Extract Mermaid blocks
                mermaid_blocks = re.findall(r"```mermaid\n(.*?)```", content, re.DOTALL)
                if mermaid_blocks:
                    for i, block in enumerate(mermaid_blocks):
                        st.markdown(f"**Diagram {i+1}**")
                        try:
                            _render_mermaid(block)
                        except Exception:
                            st.code(block, language="")
                st.markdown("---")
                st.markdown(content)
        else:
            st.info("Architecture document not generated yet.")

    with tab2:
        db_file = arch_files.get("DATABASE_SCHEMA.md")
        if db_file:
            content = fetch_content("DATABASE_SCHEMA.md")
            if content:
                er_blocks = re.findall(r"```mermaid\n(.*?)```", content, re.DOTALL)
                if er_blocks:
                    st.markdown("**Entity Relationship Diagram**")
                    try:
                        _render_mermaid(er_blocks[0])
                    except Exception:
                        st.code(er_blocks[0])
                sql_blocks = re.findall(r"```sql\n(.*?)```", content, re.DOTALL)
                if sql_blocks:
                    st.markdown("**SQL DDL**")
                    st.code(sql_blocks[0], language="sql")
        else:
            st.info("Database schema not generated yet.")

    with tab3:
        api_file = arch_files.get("openapi.yaml")
        if api_file:
            content = fetch_content("openapi.yaml")
            if content:
                yaml_blocks = re.findall(r"```yaml\n(.*?)```", content, re.DOTALL)
                yaml_content = yaml_blocks[0] if yaml_blocks else content
                st.code(yaml_content, language="yaml")
                st.download_button(
                    "⬇️ Download openapi.yaml",
                    data=yaml_content,
                    file_name="openapi.yaml",
                    mime="text/yaml",
                )
        else:
            st.info("API specification not generated yet.")

    with tab4:
        stack_file = arch_files.get("TECH_STACK.md")
        if stack_file:
            content = fetch_content("TECH_STACK.md")
            if content:
                st.markdown(content)
        else:
            st.info("Tech stack document not generated yet.")
