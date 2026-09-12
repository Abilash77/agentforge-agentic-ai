"""
AgentForge Streamlit Multi-Page App Entry Point.
Run with: streamlit run agentforge/frontend/app.py
"""

import streamlit as st

# Page config must be first
st.set_page_config(
    page_title="AgentForge — Multi-Agent AI Software Engineering Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/agentforge/agentforge",
        "Report a bug": "https://github.com/agentforge/agentforge/issues",
        "About": "AgentForge — Multi-Agent AI Software Engineering Platform v1.0.0",
    },
)

import requests
from agentforge.frontend.styles import inject_styles
from agentforge.frontend.pages import architecture, history, home, monitoring, project_dashboard


def _api_status() -> bool:
    try:
        r = requests.get("http://localhost:8001/health", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def render_sidebar():
    """Render the sidebar navigation."""
    inject_styles()

    with st.sidebar:
        # Logo + Branding
        st.markdown("""
        <div style="text-align:center;padding:1rem 0 1.5rem;">
            <div style="font-size:2.5rem;">⚡</div>
            <div style="font-size:1.3rem;font-weight:800;background:linear-gradient(135deg,#63b3ed,#9f7aea);
                        -webkit-background-clip:text;-webkit-text-fill-color:transparent;">AgentForge</div>
            <div style="font-size:0.85rem;color:#E2E8F0;margin-top:0.2rem;line-height:1.3;">Multi-Agent AI Software Engineering Platform</div>
            <div style="font-size:0.75rem;color:#A0AEC0;margin-top:0.5rem;font-style:italic;">Built by Aruva Abilash</div>
        </div>
        """, unsafe_allow_html=True)

        # API Status indicator
        api_ok = _api_status()
        status_color = "#68d391" if api_ok else "#fc8181"
        status_text = "API Connected" if api_ok else "API Offline"
        st.markdown(
            f'<div style="text-align:center;margin-bottom:1.5rem;">'
            f'<span style="display:inline-block;width:8px;height:8px;border-radius:50%;'
            f'background:{status_color};margin-right:6px;"></span>'
            f'<span style="font-size:0.78rem;color:{status_color};">{status_text}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Navigation
        st.markdown('<div style="font-size:0.7rem;color:#718096;text-transform:uppercase;'
                    'letter-spacing:0.1em;margin-bottom:0.5rem;">Navigation</div>',
                    unsafe_allow_html=True)

        pages = {
            "🏠 Home": "home",
            "📊 Project Dashboard": "dashboard",
            "📜 History": "history",
            "📈 Monitoring": "monitoring",
            "🏗️ Architecture": "architecture",
        }
        if "current_page" not in st.session_state:
            st.session_state["current_page"] = "home"

        for label, page_key in pages.items():
            is_active = st.session_state["current_page"] == page_key
            btn_style = "primary" if is_active else "secondary"
            if st.button(label, key=f"nav_{page_key}", use_container_width=True, type=btn_style):
                st.session_state["current_page"] = page_key
                st.rerun()

        # Active project info
        active_id = st.session_state.get("active_project_id", "")
        if active_id:
            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown('<div style="font-size:0.7rem;color:#718096;text-transform:uppercase;">Active Project</div>',
                        unsafe_allow_html=True)
            name = st.session_state.get("active_project_name", active_id[:12] + "...")
            st.markdown(
                f'<div class="af-card" style="padding:0.8rem;margin-top:0.5rem;">'
                f'<div style="font-weight:700;font-size:0.9rem;">{name}</div>'
                f'<div style="font-size:0.75rem;color:#718096;margin-top:0.2rem;">'
                f'<code>{active_id[:16]}...</code></div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # Footer
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown(
            '<div style="text-align:center;font-size:0.8rem;color:#D1D5DB;line-height:1.6;margin-top:2rem;">'
            '<strong>AgentForge</strong> — Multi-Agent AI Software Engineering Platform<br>'
            '<span style="color:#9CA3AF;">Built by Aruva Abilash</span><br>'
            '<span style="color:#6B7280;font-size:0.75rem;">v1.0.0</span>'
            '</div>',
            unsafe_allow_html=True,
        )


def main():
    """Main app entry point."""
    render_sidebar()

    # Route to page
    page = st.session_state.get("current_page", "home")
    page_map = {
        "home": home.show,
        "dashboard": project_dashboard.show,
        "history": history.show,
        "monitoring": monitoring.show,
        "architecture": architecture.show,
    }
    page_fn = page_map.get(page, home.show)
    page_fn()


if __name__ == "__main__":
    main()
