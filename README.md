# AgentForge

AgentForge is a Multi-Agent AI Software Engineering Platform built by Abilash Aruva. 
It acts as an orchestration layer that takes natural language requirements and converts them into production-ready code through requirement analysis, architecture design, code generation, testing, and deployment planning.

## Features

- **Multi-Agent Pipeline**: Specialized AI roles (Product Manager, Architect, Developer, QA, DevOps) collaboratively build software.
- **Real-Time Monitoring**: Streamlit frontend connects via WebSockets to provide live terminal logs, cost updates, and progress tracking.
- **RAG & Persistent Memory**: Integrates ChromaDB and SQLite to maintain project history and context across agent executions.
- **Cost Tracking**: Tracks LLM token usage and ensures projects stay within configurable budgets.

## Architecture

- **Frontend**: Streamlit
- **Backend**: FastAPI
- **Database**: SQLite & ChromaDB
- **Engine**: MetaGPT

## Getting Started

1. Set up your `.env` file with your preferred LLM provider (e.g., Gemini, OpenAI).
2. Start the FastAPI backend:
   ```bash
   python -m uvicorn agentforge.api.main:app --host 0.0.0.0 --port 8001
   ```
3. Start the Streamlit frontend:
   ```bash
   streamlit run agentforge/frontend/app.py
   ```
4. Navigate to `http://localhost:8501` and launch a new project!

## Acknowledgments & Attribution

AgentForge is powered by MetaGPT, a powerful multi-agent framework. The underlying MetaGPT framework is distributed under the MIT License.
