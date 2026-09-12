"""
AgentForge Output Collector.

Aggregates all generated files from a pipeline run
and packages them into a downloadable ZIP archive.
"""

from __future__ import annotations

import io
import json
import os
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from agentforge.config import get_config
from agentforge.database.database import get_session
from agentforge.database.repository import FileRepository, ProjectRepository
from agentforge.monitoring.logger import get_logger

logger = get_logger(__name__)


class OutputCollector:
    """
    Collects and packages all generated project files.

    Supports:
    - ZIP archive creation with organized folder structure
    - File listing with metadata
    - Content retrieval by filename
    - Project summary report generation
    """

    def __init__(self, project_id: str) -> None:
        self.project_id = project_id
        self._cfg = get_config()
        self._outputs_dir = Path(self._cfg.outputs_dir) / project_id
        self._outputs_dir.mkdir(parents=True, exist_ok=True)

    async def get_all_files(self) -> list[dict]:
        """Retrieve all generated files for this project from SQLite."""
        async with get_session() as session:
            repo = FileRepository(session)
            files = await repo.list_for_project(self.project_id)
            return [
                {
                    "id": f.id,
                    "filename": f.filename,
                    "file_type": f.file_type,
                    "agent_role": f.agent_role,
                    "language": f.language,
                    "size_bytes": f.size_bytes,
                    "version": f.version,
                    "created_at": f.created_at.isoformat(),
                    "content": f.content,
                }
                for f in files
            ]

    async def get_file_content(self, filename: str) -> Optional[str]:
        """Get the content of a specific file by name."""
        async with get_session() as session:
            repo = FileRepository(session)
            file = await repo.get_by_filename(self.project_id, filename)
            return file.content if file else None

    async def create_zip_package(self) -> str:
        """
        Create a ZIP archive of all generated files.

        Organizes files by agent role in subdirectories:
          project-name/
            ├── 01_product_manager/
            │   ├── BRD.md
            │   ├── SRS.md
            │   └── ...
            ├── 02_solution_architect/
            ├── 03_developer/
            ├── 04_qa/
            ├── 05_documentation/
            ├── 06_devops/
            ├── 07_presentations/
            └── project_summary.json

        Returns:
            Path to the created ZIP file
        """
        files = await self.get_all_files()

        # Get project info
        async with get_session() as session:
            repo = ProjectRepository(session)
            project = await repo.get_by_id(self.project_id)

        project_name = project.name.replace(" ", "_").lower() if project else self.project_id
        zip_filename = f"{project_name}_agentforge_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        zip_path = str(self._outputs_dir / zip_filename)

        # Agent role → subfolder mapping
        role_folders = {
            "product_manager": "01_product_manager",
            "solution_architect": "02_solution_architect",
            "developer": "03_developer",
            "qa_engineer": "04_qa",
            "documentation": "05_documentation",
            "devops": "06_devops",
            "ppt": "07_presentations",
        }

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for file in files:
                role = file.get("agent_role", "misc")
                subfolder = role_folders.get(role, "misc")
                zip_path_in_archive = f"{project_name}/{subfolder}/{file['filename']}"
                try:
                    content = file["content"]
                    if isinstance(content, str):
                        zf.writestr(zip_path_in_archive, content.encode("utf-8"))
                    else:
                        zf.writestr(zip_path_in_archive, content)
                except Exception as e:
                    logger.warning(f"Could not add {file['filename']} to ZIP: {e}")

            # Add project summary
            summary = await self._generate_project_summary()
            zf.writestr(
                f"{project_name}/project_summary.json",
                json.dumps(summary, indent=2).encode("utf-8"),
            )

            # Add README at root
            readme = await self.get_file_content("README.md")
            if readme:
                zf.writestr(f"{project_name}/README.md", readme.encode("utf-8"))

        # Write ZIP to disk
        zip_bytes = buf.getvalue()
        with open(zip_path, "wb") as f:
            f.write(zip_bytes)

        logger.info(f"ZIP package created: {zip_path} ({len(zip_bytes):,} bytes, {len(files)} files)")
        return zip_path

    async def get_zip_bytes(self) -> Optional[bytes]:
        """Return the most recent ZIP file as bytes."""
        zip_files = sorted(
            self._outputs_dir.glob("*.zip"),
            key=os.path.getmtime,
            reverse=True,
        )
        if not zip_files:
            # Create one now
            zip_path = await self.create_zip_package()
            with open(zip_path, "rb") as f:
                return f.read()

        with open(zip_files[0], "rb") as f:
            return f.read()

    async def _generate_project_summary(self) -> dict:
        """Generate a project summary JSON."""
        files = await self.get_all_files()

        files_by_agent: dict = {}
        for f in files:
            role = f.get("agent_role", "misc")
            if role not in files_by_agent:
                files_by_agent[role] = []
            files_by_agent[role].append({
                "filename": f["filename"],
                "file_type": f["file_type"],
                "size_bytes": f["size_bytes"],
            })

        async with get_session() as session:
            proj_repo = ProjectRepository(session)
            project = await proj_repo.get_by_id(self.project_id)

        return {
            "project_id": self.project_id,
            "project_name": project.name if project else "Unknown",
            "idea": project.idea if project else "Unknown",
            "tech_stack": project.tech_stack if project else "Unknown",
            "status": project.status if project else "Unknown",
            "total_files": len(files),
            "total_tokens": project.total_tokens if project else 0,
            "total_cost_usd": project.total_cost_usd if project else 0.0,
            "generated_at": datetime.utcnow().isoformat(),
            "files_by_agent": files_by_agent,
            "generated_by": "AgentForge v1.0.0",
        }
