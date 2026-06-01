"""WebSocket manager for real-time client updates."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections to frontend clients."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, event: str, data: Any) -> None:
        """Broadcast an event to all connected clients."""
        message = json.dumps(
            {
                "event": event,
                "data": _serialize(data),
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        disconnected: list[WebSocket] = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)

    async def send_personal(self, websocket: WebSocket, event: str, data: Any) -> None:
        """Send a message to a specific client."""
        message = json.dumps(
            {
                "event": event,
                "data": _serialize(data),
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        try:
            await websocket.send_text(message)
        except Exception:
            self.disconnect(websocket)


def _serialize(obj: Any) -> Any:
    """Serialize objects for JSON."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize(i) for i in obj]
    return obj
