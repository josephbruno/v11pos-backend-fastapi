"""
WebSocket Service for Real-time KDS Updates
Provides live updates between Kitchen Display System and POS
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set
from datetime import datetime
import json
import asyncio


class KDSConnectionManager:
    """Manages WebSocket connections for KDS real-time updates"""
    
    def __init__(self):
        # Store active connections by restaurant_id and station_id
        # Format: {restaurant_id: {station_id: [WebSocket, WebSocket, ...]}}
        self.restaurant_connections: Dict[str, Dict[str, List[WebSocket]]] = {}
        
        # Store POS connections by restaurant_id
        # Format: {restaurant_id: [WebSocket, WebSocket, ...]}
        self.pos_connections: Dict[str, List[WebSocket]] = {}
        
        # Store admin connections (can receive all updates)
        self.admin_connections: List[WebSocket] = []
    
    async def connect_station(self, websocket: WebSocket, restaurant_id: str, station_id: str):
        """Connect a kitchen display station"""
        await websocket.accept()
        
        if restaurant_id not in self.restaurant_connections:
            self.restaurant_connections[restaurant_id] = {}
        
        if station_id not in self.restaurant_connections[restaurant_id]:
            self.restaurant_connections[restaurant_id][station_id] = []
        
        self.restaurant_connections[restaurant_id][station_id].append(websocket)
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "restaurant_id": restaurant_id,
            "station_id": station_id,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def connect_pos(self, websocket: WebSocket, restaurant_id: str):
        """Connect a POS terminal"""
        await websocket.accept()
        
        if restaurant_id not in self.pos_connections:
            self.pos_connections[restaurant_id] = []
        
        self.pos_connections[restaurant_id].append(websocket)
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "role": "pos",
            "restaurant_id": restaurant_id,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def connect_admin(self, websocket: WebSocket):
        """Connect an admin monitor"""
        await websocket.accept()
        self.admin_connections.append(websocket)
        
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "role": "admin",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def disconnect_station(self, websocket: WebSocket, restaurant_id: str, station_id: str):
        """Disconnect a kitchen display station"""
        if restaurant_id in self.restaurant_connections:
            if station_id in self.restaurant_connections[restaurant_id]:
                if websocket in self.restaurant_connections[restaurant_id][station_id]:
                    self.restaurant_connections[restaurant_id][station_id].remove(websocket)
                
                # Cleanup empty lists
                if not self.restaurant_connections[restaurant_id][station_id]:
                    del self.restaurant_connections[restaurant_id][station_id]
            
            if not self.restaurant_connections[restaurant_id]:
                del self.restaurant_connections[restaurant_id]
    
    def disconnect_pos(self, websocket: WebSocket, restaurant_id: str):
        """Disconnect a POS terminal"""
        if restaurant_id in self.pos_connections:
            if websocket in self.pos_connections[restaurant_id]:
                self.pos_connections[restaurant_id].remove(websocket)
            
            if not self.pos_connections[restaurant_id]:
                del self.pos_connections[restaurant_id]
    
    def disconnect_admin(self, websocket: WebSocket):
        """Disconnect an admin monitor"""
        if websocket in self.admin_connections:
            self.admin_connections.remove(websocket)
    
    async def broadcast_to_station(self, restaurant_id: str, station_id: str, message: dict):
        """Broadcast message to all connections of a specific station"""
        if restaurant_id in self.restaurant_connections:
            if station_id in self.restaurant_connections[restaurant_id]:
                disconnected = []
                
                for connection in self.restaurant_connections[restaurant_id][station_id]:
                    try:
                        await connection.send_json(message)
                    except:
                        disconnected.append(connection)
                
                # Remove disconnected connections
                for conn in disconnected:
                    self.disconnect_station(conn, restaurant_id, station_id)
    
    async def broadcast_to_restaurant_stations(self, restaurant_id: str, message: dict):
        """Broadcast message to all stations of a restaurant"""
        if restaurant_id in self.restaurant_connections:
            for station_id in self.restaurant_connections[restaurant_id]:
                await self.broadcast_to_station(restaurant_id, station_id, message)
    
    async def broadcast_to_pos(self, restaurant_id: str, message: dict):
        """Broadcast message to all POS terminals of a restaurant"""
        if restaurant_id in self.pos_connections:
            disconnected = []
            
            for connection in self.pos_connections[restaurant_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.append(connection)
            
            # Remove disconnected connections
            for conn in disconnected:
                self.disconnect_pos(conn, restaurant_id)
    
    async def broadcast_to_admins(self, message: dict):
        """Broadcast message to all admin monitors"""
        disconnected = []
        
        for connection in self.admin_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)
        
        # Remove disconnected connections
        for conn in disconnected:
            self.disconnect_admin(conn)
    
    async def notify_new_order(self, restaurant_id: str, station_id: str, display_data: dict):
        """Notify station about new order"""
        message = {
            "type": "new_order",
            "restaurant_id": restaurant_id,
            "station_id": station_id,
            "display": display_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast_to_station(restaurant_id, station_id, message)
        await self.broadcast_to_admins(message)
    
    async def notify_status_change(
        self,
        restaurant_id: str,
        station_id: str,
        display_id: str,
        old_status: str,
        new_status: str,
        display_data: dict = None
    ):
        """Notify about display status change"""
        message = {
            "type": "status_change",
            "restaurant_id": restaurant_id,
            "station_id": station_id,
            "display_id": display_id,
            "old_status": old_status,
            "new_status": new_status,
            "display": display_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Notify the station
        await self.broadcast_to_station(restaurant_id, station_id, message)
        
        # Notify POS terminals
        await self.broadcast_to_pos(restaurant_id, message)
        
        # Notify admins
        await self.broadcast_to_admins(message)
    
    async def notify_item_status_change(
        self,
        restaurant_id: str,
        station_id: str,
        display_id: str,
        item_id: str,
        old_status: str,
        new_status: str
    ):
        """Notify about item status change"""
        message = {
            "type": "item_status_change",
            "restaurant_id": restaurant_id,
            "station_id": station_id,
            "display_id": display_id,
            "item_id": item_id,
            "old_status": old_status,
            "new_status": new_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast_to_station(restaurant_id, station_id, message)
        await self.broadcast_to_pos(restaurant_id, message)
        await self.broadcast_to_admins(message)
    
    async def notify_order_completed(self, restaurant_id: str, order_id: str, order_data: dict):
        """Notify POS that an order is ready"""
        message = {
            "type": "order_ready",
            "restaurant_id": restaurant_id,
            "order_id": order_id,
            "order": order_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast_to_pos(restaurant_id, message)
        await self.broadcast_to_admins(message)
    
    async def notify_order_delayed(
        self,
        restaurant_id: str,
        station_id: str,
        display_id: str,
        delay_minutes: int
    ):
        """Notify about order delay"""
        message = {
            "type": "order_delayed",
            "restaurant_id": restaurant_id,
            "station_id": station_id,
            "display_id": display_id,
            "delay_minutes": delay_minutes,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast_to_station(restaurant_id, station_id, message)
        await self.broadcast_to_pos(restaurant_id, message)
        await self.broadcast_to_admins(message)
    
    async def send_heartbeat(self):
        """Send periodic heartbeat to all connections"""
        message = {
            "type": "heartbeat",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send to all station connections
        for restaurant_id in list(self.restaurant_connections.keys()):
            await self.broadcast_to_restaurant_stations(restaurant_id, message)
        
        # Send to all POS connections
        for restaurant_id in list(self.pos_connections.keys()):
            await self.broadcast_to_pos(restaurant_id, message)
        
        # Send to admin connections
        await self.broadcast_to_admins(message)
    
    def get_active_connections_count(self, restaurant_id: str = None) -> dict:
        """Get count of active connections"""
        if restaurant_id:
            station_count = sum(
                len(connections)
                for station_id, connections in self.restaurant_connections.get(restaurant_id, {}).items()
            )
            pos_count = len(self.pos_connections.get(restaurant_id, []))
            
            return {
                "restaurant_id": restaurant_id,
                "stations": station_count,
                "pos_terminals": pos_count,
                "total": station_count + pos_count
            }
        else:
            total_stations = sum(
                len(connections)
                for restaurant in self.restaurant_connections.values()
                for connections in restaurant.values()
            )
            total_pos = sum(len(connections) for connections in self.pos_connections.values())
            
            return {
                "total_stations": total_stations,
                "total_pos_terminals": total_pos,
                "total_admins": len(self.admin_connections),
                "total": total_stations + total_pos + len(self.admin_connections)
            }


# Global instance
kds_manager = KDSConnectionManager()


async def heartbeat_task():
    """Background task to send periodic heartbeats"""
    while True:
        await asyncio.sleep(30)  # Send heartbeat every 30 seconds
        await kds_manager.send_heartbeat()
