"""
AgentForge Home Page.

Landing page where users enter their project idea and start the pipeline.
"""

import time

import requests
import streamlit as st

from agentforge.frontend.styles import inject_styles

API_BASE = "http://localhost:8001"

PROJECT_TYPES = [
    ("🌐 Full Stack Web App", "full_stack"),
    ("🔌 REST API Service", "api_service"),
    ("📱 Mobile App Backend", "mobile_app"),
    ("🤖 SaaS Platform", "saas_platform"),
    ("📊 Data Pipeline", "data_pipeline"),
    ("🛒 E-Commerce Platform", "ecommerce"),
    ("🧠 ML Model Service", "ml_model"),
    ("⚡ Microservice", "microservice"),
    ("🖥️ CLI Tool", "cli_tool"),
]

TECH_STACKS = [
    ("⚡ FastAPI + React (Recommended)", "fastapi_react"),
    ("🐍 Django + React", "django_react"),
    ("🟩 Node.js + Next.js (PERN)", "pern"),
    ("🍃 Node.js + Vue (MERN)", "mern"),
    ("🌿 Node.js + Angular (MEAN)", "mean"),
    ("☕ Spring Boot + React", "java_spring"),
    ("🐹 Go + React", "go_gin"),
]

EXAMPLE_IDEAS = [
    "Build a URL shortener with analytics dashboard, user authentication, and click tracking",
    "Create a real-time collaborative task management app with teams, deadlines, and notifications",
    "Develop an AI-powered code review platform that integrates with GitHub PRs",
    "Build a multi-tenant SaaS invoicing platform with Stripe payments and PDF generation",
    "Create a social platform for developers to share code snippets and projects",
]


def show():
    inject_styles()

    # ── Hero Section ─────────────────────────────────────────────────────────
    st.markdown("""
    <div class="hero">
        <h1>⚡ AgentForge</h1>
        <p style="font-size:1.1rem; color:#E2E8F0; font-weight:500; margin-bottom:0.2rem;">Multi-Agent AI Software Engineering Platform</p>
        <p style="font-size:0.9rem; color:#A0AEC0; font-style:italic;">Built by Aruva Abilash</p>
        <p style="font-size:0.95rem; margin-top:1rem; color:#718096;">
            7 AI agents collaborate to transform your idea into production-ready software
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Agent Pipeline Overview ───────────────────────────────────────────────
    st.markdown("""
    <div style="display:flex; gap:0.5rem; justify-content:center; flex-wrap:wrap; margin-bottom:2rem;">
        <div style="background:rgba(99,179,237,0.1);border:1px solid rgba(99,179,237,0.3);
                    border-radius:8px;padding:0.4rem 0.8rem;font-size:0.8rem;color:#63b3ed;">
            👩‍💼 Product Manager
        </div>
        <div style="color:#718096;font-size:1.2rem;">→</div>
        <div style="background:rgba(159,122,234,0.1);border:1px solid rgba(159,122,234,0.3);
                    border-radius:8px;padding:0.4rem 0.8rem;font-size:0.8rem;color:#9f7aea;">
            🏗️ Solution Architect
        </div>
        <div style="color:#718096;font-size:1.2rem;">→</div>
        <div style="background:rgba(104,211,145,0.1);border:1px solid rgba(104,211,145,0.3);
                    border-radius:8px;padding:0.4rem 0.8rem;font-size:0.8rem;color:#68d391;">
            💻 Developer
        </div>
        <div style="color:#718096;font-size:1.2rem;">→</div>
        <div style="background:rgba(246,173,85,0.1);border:1px solid rgba(246,173,85,0.3);
                    border-radius:8px;padding:0.4rem 0.8rem;font-size:0.8rem;color:#f6ad55;">
            🧪 QA Engineer
        </div>
        <div style="color:#718096;font-size:1.2rem;">→</div>
        <div style="background:rgba(99,179,237,0.1);border:1px solid rgba(99,179,237,0.3);
                    border-radius:8px;padding:0.4rem 0.8rem;font-size:0.8rem;color:#63b3ed;">
            📝 Docs
        </div>
        <div style="color:#718096;font-size:1.2rem;">→</div>
        <div style="background:rgba(252,129,129,0.1);border:1px solid rgba(252,129,129,0.3);
                    border-radius:8px;padding:0.4rem 0.8rem;font-size:0.8rem;color:#fc8181;">
            🐳 DevOps
        </div>
        <div style="color:#718096;font-size:1.2rem;">→</div>
        <div style="background:rgba(159,122,234,0.1);border:1px solid rgba(159,122,234,0.3);
                    border-radius:8px;padding:0.4rem 0.8rem;font-size:0.8rem;color:#9f7aea;">
            📊 PPT
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Project Form ──────────────────────────────────────────────────────────
    with st.container():
        st.markdown('<div class="section-header">🚀 Launch New Project</div>', unsafe_allow_html=True)

        col1, col2 = st.columns([1, 1])
        with col1:
            project_name = st.text_input(
                "Project Name",
                placeholder="e.g., TaskFlow Pro",
                key="home_project_name",
            )
        with col2:
            # Example ideas
            example_idx = st.selectbox(
                "💡 Load example idea",
                ["(Custom idea)"] + EXAMPLE_IDEAS,
                key="home_example",
            )

        # Idea text area
        default_idea = "" if example_idx == "(Custom idea)" else example_idx
        idea = st.text_area(
            "Your Project Idea",
            value=default_idea,
            height=140,
            placeholder="Describe what you want to build. Be specific about features, users, and goals...",
            key="home_idea",
        )

        col3, col4 = st.columns([1, 1])
        with col3:
            project_type_label = st.selectbox(
                "Software Type",
                [t[0] for t in PROJECT_TYPES],
                key="home_project_type",
            )
            project_type = next(t[1] for t in PROJECT_TYPES if t[0] == project_type_label)

        with col4:
            stack_label = st.selectbox(
                "Technology Stack",
                [t[0] for t in TECH_STACKS],
                key="home_tech_stack",
            )
            tech_stack = next(t[1] for t in TECH_STACKS if t[0] == stack_label)

        col5, col6 = st.columns([1, 1])
        with col5:
            budget = st.slider("💰 Budget (USD)", min_value=1.0, max_value=20.0, value=5.0, step=0.5)
        with col6:
            priority = st.select_slider("⚡ Priority", options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], value=5)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Launch Button ─────────────────────────────────────────────────────
        launch_col, status_col = st.columns([1, 2])
        with launch_col:
            launch = st.button("🚀 Launch AgentForge", use_container_width=True, type="primary")

        if launch:
            if not idea.strip():
                st.error("❌ Please enter a project idea")
            elif not project_name.strip():
                st.error("❌ Please enter a project name")
            elif len(idea.strip()) < 20:
                st.error("❌ Please provide a more detailed idea (at least 20 characters)")
            else:
                with st.spinner("Submitting project to AgentForge..."):
                    try:
                        response = requests.post(
                            f"{API_BASE}/api/v1/projects",
                            json={
                                "name": project_name.strip(),
                                "idea": idea.strip(),
                                "project_type": project_type,
                                "tech_stack": tech_stack,
                                "budget_usd": budget,
                                "priority": priority,
                            },
                            timeout=15,
                        )
                        if response.status_code == 201:
                            project = response.json()
                            st.success(f"✅ Project '{project_name}' launched! ID: `{project['id']}`")
                            st.info("👇 Go to **Project Dashboard** to track progress in real-time.")
                            st.session_state["active_project_id"] = project["id"]
                            st.session_state["active_project_name"] = project_name
                            st.session_state["current_page"] = "dashboard"
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"❌ API Error: {response.status_code} — {response.text[:200]}")
                    except requests.exceptions.ConnectionError:
                        st.error("❌ Cannot connect to AgentForge API. Make sure the API server is running on port 8001.")
                    except Exception as e:
                        st.error(f"❌ Unexpected error: {e}")

    # ── What AgentForge Generates ─────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">📦 What AgentForge Generates</div>', unsafe_allow_html=True)

    deliverables = [
        ("📋", "BRD & SRS", "Business requirements and software specification"),
        ("🏗️", "Architecture", "C4 diagrams, database schema, API spec"),
        ("💻", "Source Code", "Backend + Frontend complete implementation"),
        ("🧪", "Tests", "Unit, integration, and E2E test suites"),
        ("📝", "Documentation", "README, setup guide, API reference"),
        ("🐳", "DevOps", "Docker, CI/CD, Kubernetes manifests"),
        ("📊", "Presentations", "Pitch deck, hackathon and investor slides"),
        ("⬇️", "ZIP Package", "Download everything in one archive"),
    ]

    cols = st.columns(4)
    for i, (icon, title, desc) in enumerate(deliverables):
        with cols[i % 4]:
            st.markdown(
                f'<div class="af-card" style="text-align:center;padding:1rem;">'
                f'<div style="font-size:2rem;">{icon}</div>'
                f'<div style="font-weight:700;font-size:0.95rem;margin:0.3rem 0;">{title}</div>'
                f'<div style="font-size:0.8rem;color:#718096;">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
