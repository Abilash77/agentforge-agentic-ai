"""
AgentForge Streamlit Custom Styles.

Dark glassmorphism theme injected via st.markdown.
"""

AGENTFORGE_CSS = """
<style>
/* ─── Google Fonts ─────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Fira+Code:wght@400;500&display=swap');

/* ─── Root Variables ────────────────────────────────────── */
:root {
  --bg-primary: #0a0e1a;
  --bg-secondary: #0f1629;
  --bg-card: rgba(255,255,255,0.04);
  --bg-card-hover: rgba(255,255,255,0.07);
  --border: rgba(255,255,255,0.08);
  --border-accent: rgba(99,179,237,0.3);
  --accent-primary: #63b3ed;
  --accent-secondary: #9f7aea;
  --accent-success: #68d391;
  --accent-warning: #f6ad55;
  --accent-danger: #fc8181;
  --text-primary: #e2e8f0;
  --text-secondary: #a0aec0;
  --text-muted: #718096;
  --gradient-1: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --gradient-2: linear-gradient(135deg, #63b3ed 0%, #9f7aea 100%);
  --gradient-3: linear-gradient(135deg, #68d391 0%, #63b3ed 100%);
  --shadow: 0 8px 32px rgba(0,0,0,0.4);
  --shadow-sm: 0 2px 8px rgba(0,0,0,0.3);
}

/* ─── Global ────────────────────────────────────────────── */
.stApp {
  font-family: 'Inter', sans-serif !important;
  background: var(--bg-primary) !important;
  color: var(--text-primary) !important;
}

/* ─── Sidebar ───────────────────────────────────────────── */
[data-testid="stSidebar"] {
  background: var(--bg-secondary) !important;
  border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] .stMarkdown h1,
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 {
  color: var(--accent-primary) !important;
}

/* ─── Buttons ───────────────────────────────────────────── */
.stButton > button {
  background: var(--gradient-2) !important;
  color: white !important;
  border: none !important;
  border-radius: 8px !important;
  font-weight: 600 !important;
  font-size: 0.9rem !important;
  padding: 0.5rem 1.5rem !important;
  transition: all 0.2s ease !important;
  box-shadow: var(--shadow-sm) !important;
}
.stButton > button:hover {
  transform: translateY(-2px) !important;
  box-shadow: var(--shadow) !important;
  opacity: 0.9 !important;
}

/* ─── Cards ─────────────────────────────────────────────── */
.af-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 1.5rem;
  backdrop-filter: blur(10px);
  transition: all 0.2s ease;
  margin-bottom: 1rem;
}
.af-card:hover {
  background: var(--bg-card-hover);
  border-color: var(--border-accent);
  box-shadow: var(--shadow);
  transform: translateY(-2px);
}

/* ─── Agent Cards ───────────────────────────────────────── */
.agent-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1rem;
  margin: 0.5rem 0;
  transition: all 0.3s ease;
}
.agent-card.running {
  border-color: var(--accent-primary);
  box-shadow: 0 0 20px rgba(99,179,237,0.2);
  animation: pulse-border 2s infinite;
}
.agent-card.completed {
  border-color: var(--accent-success);
}
.agent-card.failed {
  border-color: var(--accent-danger);
}

@keyframes pulse-border {
  0%, 100% { box-shadow: 0 0 15px rgba(99,179,237,0.2); }
  50% { box-shadow: 0 0 25px rgba(99,179,237,0.4); }
}

/* ─── Metric Cards ──────────────────────────────────────── */
.metric-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.2rem 1.5rem;
  text-align: center;
}
.metric-value {
  font-size: 2rem;
  font-weight: 800;
  background: var(--gradient-2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.metric-label {
  font-size: 0.8rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-top: 0.3rem;
}

/* ─── Progress Bars ─────────────────────────────────────── */
.stProgress > div > div > div > div {
  background: var(--gradient-2) !important;
  border-radius: 100px !important;
}
.stProgress > div > div > div {
  background: rgba(255,255,255,0.08) !important;
  border-radius: 100px !important;
}

/* ─── Text Inputs ───────────────────────────────────────── */
.stTextInput input, .stTextArea textarea, .stSelectbox select {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  color: #ffffff !important;
}
.stTextInput input::placeholder, .stTextArea textarea::placeholder {
  color: #a0aec0 !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
  border-color: var(--accent-primary) !important;
  box-shadow: 0 0 0 2px rgba(99,179,237,0.2) !important;
}

/* ─── Sidebar Navigation ────────────────────────────────── */
[data-testid="stSidebarNav"] span {
  color: #a0aec0 !important;
}
[data-testid="stSidebarNav"] a:hover span {
  color: #ffffff !important;
}
[data-testid="stSidebarNav"] [aria-current="page"] span {
  color: #ffffff !important;
}

/* ─── Status Badges ─────────────────────────────────────── */
.badge {
  display: inline-block;
  padding: 0.2rem 0.7rem;
  border-radius: 100px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.badge-pending    { background: rgba(160,174,192,0.15); color: #a0aec0; }
.badge-running    { background: rgba(99,179,237,0.15);  color: #63b3ed; }
.badge-completed  { background: rgba(104,211,145,0.15); color: #68d391; }
.badge-failed     { background: rgba(252,129,129,0.15); color: #fc8181; }

/* ─── File Viewer ───────────────────────────────────────── */
.file-content {
  background: #0d1117;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1rem;
  font-family: 'Fira Code', monospace;
  font-size: 0.85rem;
  color: #e6edf3;
  overflow-x: auto;
  max-height: 600px;
}

/* ─── Hero Section ──────────────────────────────────────── */
.hero {
  text-align: center;
  padding: 3rem 1rem;
  background: linear-gradient(135deg, rgba(102,126,234,0.1) 0%, rgba(118,75,162,0.1) 100%);
  border-radius: 20px;
  border: 1px solid var(--border);
  margin-bottom: 2rem;
}
.hero h1 {
  font-size: 3rem;
  font-weight: 800;
  background: var(--gradient-1);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
}
.hero p {
  color: var(--text-secondary);
  font-size: 1.1rem;
  margin-top: 0.5rem;
}

/* ─── Section Headers ───────────────────────────────────── */
.section-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--border);
}

/* ─── Code Blocks ───────────────────────────────────────── */
code {
  font-family: 'Fira Code', monospace !important;
  background: rgba(255,255,255,0.06) !important;
  border-radius: 4px !important;
  padding: 0.1em 0.4em !important;
  font-size: 0.9em !important;
}

/* ─── Tabs ──────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
  background: var(--bg-card) !important;
  border-radius: 10px !important;
  padding: 4px !important;
}
.stTabs [data-baseweb="tab"] {
  border-radius: 8px !important;
  color: var(--text-secondary) !important;
}
.stTabs [aria-selected="true"] {
  background: var(--gradient-2) !important;
  color: white !important;
}

/* ─── DataFrames ────────────────────────────────────────── */
.stDataFrame {
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
}

/* ─── Scrollbar ─────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.25); }

/* ─── Divider ───────────────────────────────────────────── */
hr { border-color: var(--border) !important; }
</style>
"""


def inject_styles() -> None:
    """Inject AgentForge CSS into the Streamlit app."""
    import streamlit as st
    st.markdown(AGENTFORGE_CSS, unsafe_allow_html=True)


def card(content: str, extra_class: str = "") -> str:
    """Return an HTML card wrapper."""
    return f'<div class="af-card {extra_class}">{content}</div>'


def badge(text: str, status: str = "pending") -> str:
    """Return an HTML status badge."""
    return f'<span class="badge badge-{status}">{text}</span>'


def metric_card(value: str, label: str) -> str:
    """Return an HTML metric card."""
    return (
        f'<div class="metric-card">'
        f'<div class="metric-value">{value}</div>'
        f'<div class="metric-label">{label}</div>'
        f'</div>'
    )
