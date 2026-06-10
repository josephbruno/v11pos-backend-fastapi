"""
WebSocket service for real-time Order updates.

Keeps connections scoped by restaurant_id so the UI can subscribe only to the
restaurant it is currently operating on.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from fastapi import WebSocket


def normalize_restaurant_id(restaurant_id: str) -> str:
    """Canonical key for connection map lookups (must match broadcast keys)."""
    return str(restaurant_id).strip()


class OrderConnectionManager:
    """Manages WebSocket connections for order updates (scoped by restaurant)."""

    def __init__(self) -> None:
        # Format: {restaurant_id: [WebSocket, WebSocket, ...]}
        self.connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, restaurant_id: str) -> None:
        restaurant_id = normalize_restaurant_id(restaurant_id)
        await websocket.accept()
        self.connections.setdefault(restaurant_id, []).append(websocket)

        await websocket.send_json(
            {
                "type": "connection",
                "status": "connected",
                "restaurant_id": restaurant_id,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    def disconnect(self, websocket: WebSocket, restaurant_id: str) -> None:
        restaurant_id = normalize_restaurant_id(restaurant_id)
        if restaurant_id not in self.connections:
            return

        if websocket in self.connections[restaurant_id]:
            self.connections[restaurant_id].remove(websocket)

        if not self.connections[restaurant_id]:
            del self.connections[restaurant_id]

    async def broadcast(self, restaurant_id: str, message: dict) -> None:
        """Broadcast to all connections for a restaurant (best-effort)."""
        restaurant_id = normalize_restaurant_id(restaurant_id)
        if restaurant_id not in self.connections:
            return

        disconnected: List[WebSocket] = []
        for websocket in self.connections[restaurant_id]:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)

        for websocket in disconnected:
            self.disconnect(websocket, restaurant_id)


order_ws_manager = OrderConnectionManager()

