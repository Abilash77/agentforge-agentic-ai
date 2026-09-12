"""
AgentForge WebSocket Handler.

Real-time progress streaming for pipeline execution.
Clients subscribe to /ws/{project_id} to receive agent progress events.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from agentforge.monitoring.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


class ConnectionManager:
    """
    Manages active WebSocket connections per project.

    Supports multiple concurrent clients watching the same project.
    Thread-safe via asyncio locks.
    """

    def __init__(self) -> None:
        # project_id → set of connected WebSocket clients
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, project_id: str) -> None:
        await websocket.accept()
        async with self._lock:
            if project_id not in self._connections:
                self._connections[project_id] = set()
            self._connections[project_id].add(websocket)
        logger.info(f"WebSocket connected: project={project_id}, total={len(self._connections[project_id])}")

    async def disconnect(self, websocket: WebSocket, project_id: str) -> None:
        async with self._lock:
            if project_id in self._connections:
                self._connections[project_id].discard(websocket)
                if not self._connections[project_id]:
                    del self._connections[project_id]

    async def broadcast(self, project_id: str, message: dict) -> None:
        """Send a message to all clients watching a project."""
        message["timestamp"] = datetime.utcnow().isoformat()
        msg_str = json.dumps(message)

        disconnected: Set[WebSocket] = set()
        connections = self._connections.get(project_id, set()).copy()

        for ws in connections:
            try:
                await ws.send_text(msg_str)
            except Exception:
                disconnected.add(ws)

        # Cleanup disconnected clients
        if disconnected:
            async with self._lock:
                for ws in disconnected:
                    self._connections.get(project_id, set()).discard(ws)

    async def send_to_project(self, project_id: str, event: dict) -> None:
        """Public method called by the pipeline progress callback."""
        await self.broadcast(project_id, event)

    def get_connection_count(self, project_id: str) -> int:
        return len(self._connections.get(project_id, set()))

    def get_all_projects(self) -> list[str]:
        return list(self._connections.keys())


# Global singleton connection manager
ws_manager = ConnectionManager()


@router.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str) -> None:
    """
    WebSocket endpoint for real-time pipeline progress.

    Clients connect to ws://host/ws/{project_id}

    Message format:
    {
        "event": "agent_start|agent_progress|agent_complete|pipeline_complete|error",
        "agent_role": "product_manager",
        "agent": "Alexandra",
        "step": "analyze_requirements",
        "percentage": 25,
        "message": "BRD generated ✓",
        "project_id": "...",
        "timestamp": "2024-..."
    }
    """
    await ws_manager.connect(websocket, project_id)
    logger.info(f"WebSocket client connected to project {project_id}")

    try:
        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            "event": "connected",
            "project_id": project_id,
            "message": "Connected to AgentForge real-time stream",
            "timestamp": datetime.utcnow().isoformat(),
        }))

        # Keep connection alive — listen for client messages (ping/pong)
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                msg = json.loads(data)
                # Handle ping
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat(),
                    }))
            except asyncio.TimeoutError:
                # Send keepalive
                try:
                    await websocket.send_text(json.dumps({
                        "type": "keepalive",
                        "timestamp": datetime.utcnow().isoformat(),
                    }))
                except Exception:
                    break

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected from project {project_id}")
    except Exception as e:
        logger.error(f"WebSocket error for project {project_id}: {e}")
    finally:
        await ws_manager.disconnect(websocket, project_id)


def make_progress_callback(project_id: str):
    """
    Factory that returns an async callable for broadcasting pipeline progress.

    Used by the pipeline to emit events: pipeline calls await callback(event_dict)
    """
    async def callback(event: dict) -> None:
        await ws_manager.broadcast(project_id, event)

    return callback
