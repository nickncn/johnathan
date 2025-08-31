"""WebSocket streaming service for real-time data."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Set, Optional

import redis.asyncio as redis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.services.connectors import MockDataConnector

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


class ConnectionManager:
    """WebSocket connection manager with Redis pub/sub support."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.redis_client: Optional[redis.Redis] = None
        self.redis_subscriber: Optional[redis.Redis] = None
        self.subscriptions: Dict[str, Set[WebSocket]] = {}
        self._redis_listener_task: Optional[asyncio.Task] = None
    
    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")
        
        # Initialize Redis connections if not exists
        if not self.redis_client:
            await self._init_redis()
    
    async def _init_redis(self):
        """Initialize Redis connections for pub/sub."""
        try:
            self.redis_client = redis.from_url(settings.REDIS_URL)
            self.redis_subscriber = redis.from_url(settings.REDIS_URL)
            
            # Start Redis listener task
            if not self._redis_listener_task:
                self._redis_listener_task = asyncio.create_task(self._redis_listener())
                
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
    
    async def _redis_listener(self):
        """Listen for Redis pub/sub messages and broadcast to WebSocket clients."""
        if not self.redis_subscriber:
            return
            
        try:
            # Subscribe to relevant channels
            channels = ['price_updates', 'pnl_updates', 'risk_alerts']
            async with self.redis_subscriber.pubsub() as pubsub:
                for channel in channels:
                    await pubsub.subscribe(channel)
                
                logger.info(f"Subscribed to Redis channels: {channels}")
                
                async for message in pubsub.listen():
                    if message['type'] == 'message':
                        channel = message['channel'].decode()
                        data = message['data'].decode()
                        
                        # Broadcast to all connected WebSocket clients
                        await self.broadcast(data)
                        
        except Exception as e:
            logger.error(f"Redis listener error: {e}")
            # Restart listener after delay
            await asyncio.sleep(5)
            if self.redis_subscriber:
                self._redis_listener_task = asyncio.create_task(self._redis_listener())
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection and clean up subscriptions."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # Remove from all subscriptions
        for channel, subscribers in self.subscriptions.items():
            subscribers.discard(websocket)
        
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific client."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: str):
        """Broadcast message to all connected clients."""
        if not self.active_connections:
            return
            
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_json(self, data: Dict):
        """Broadcast JSON data to all clients."""
        message = json.dumps(data, default=str)  # Handle datetime serialization
        await self.broadcast(message)
    
    async def publish_to_redis(self, channel: str, data: Dict):
        """Publish message to Redis channel."""
        if self.redis_client:
            try:
                message = json.dumps(data, default=str)
                await self.redis_client.publish(channel, message)
            except Exception as e:
                logger.error(f"Redis publish error: {e}")
    
    async def subscribe_to_channel(self, websocket: WebSocket, channel: str):
        """Subscribe WebSocket client to specific channel."""
        if channel not in self.subscriptions:
            self.subscriptions[channel] = set()
        self.subscriptions[channel].add(websocket)
    
    async def unsubscribe_from_channel(self, websocket: WebSocket, channel: str):
        """Unsubscribe WebSocket client from specific channel."""
        if channel in self.subscriptions:
            self.subscriptions[channel].discard(websocket)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for streaming data."""
    await manager.connect(websocket)
    
    try:
        # Send initial connection message
        await manager.send_personal_message(
            json.dumps({
                "type": "connection",
                "status": "connected",
                "timestamp": datetime.utcnow().isoformat(),
                "available_channels": ["prices", "pnl", "alerts", "all"]
            }),
            websocket
        )
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for message from client with timeout
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                
                # Parse client message
                try:
                    client_message = json.loads(data)
                    await handle_client_message(client_message, websocket)
                except json.JSONDecodeError:
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "error",
                            "message": "Invalid JSON format"
                        }),
                        websocket
                    )
            
            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive
                await manager.send_personal_message(
                    json.dumps({
                        "type": "heartbeat",
                        "timestamp": datetime.utcnow().isoformat()
                    }),
                    websocket
                )
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await manager.send_personal_message(
                    json.dumps({
                        "type": "error",
                        "message": "Internal server error"
                    }),
                    websocket
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        manager.disconnect(websocket)


async def handle_client_message(message: Dict, websocket: WebSocket):
    """Handle incoming client messages."""
    msg_type = message.get("type")
    
    if msg_type == "subscribe":
        # Handle subscription to data feeds
        channels = message.get("channels", [])
        for channel in channels:
            await manager.subscribe_to_channel(websocket, channel)
        
        await manager.send_personal_message(
            json.dumps({
                "type": "subscription",
                "status": "subscribed",
                "channels": channels,
                "timestamp": datetime.utcnow().isoformat()
            }),
            websocket
        )
    
    elif msg_type == "unsubscribe":
        # Handle unsubscription from data feeds
        channels = message.get("channels", [])
        for channel in channels:
            await manager.unsubscribe_from_channel(websocket, channel)
        
        await manager.send_personal_message(
            json.dumps({
                "type": "unsubscription", 
                "status": "unsubscribed",
                "channels": channels,
                "timestamp": datetime.utcnow().isoformat()
            }),
            websocket
        )
    
    elif msg_type == "ping":
        # Respond to ping with pong
        await manager.send_personal_message(
            json.dumps({
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat()
            }),
            websocket
        )
    
    elif msg_type == "get_status":
        # Send current status
        await manager.send_personal_message(
            json.dumps({
                "type": "status",
                "connected_clients": len(manager.active_connections),
                "active_subscriptions": {
                    channel: len(subscribers) 
                    for channel, subscribers in manager.subscriptions.items()
                },
                "timestamp": datetime.utcnow().isoformat()
            }),
            websocket
        )
    
    else:
        await manager.send_personal_message(
            json.dumps({
                "type": "error",
                "message": f"Unknown message type: {msg_type}",
                "timestamp": datetime.utcnow().isoformat()
            }),
            websocket
        )


# Streaming data functions
async def stream_price_updates():
    """Stream live price updates."""
    logger.info("Starting price update stream...")
    
    async with AsyncSessionLocal() as db:
        connector = MockDataConnector(db)
        
        symbols = ['AAPL', 'GOOGL', 'TSLA', 'MSFT', 'AMZN', 'BTC', 'ETH', 'ADA']
        
        while True:
            try:
                # Generate price updates for all symbols
                price_updates = []
                for symbol in symbols:
                    tick_data = await connector.generate_live_tick(symbol)
                    price_updates.append(tick_data)
                
                message = {
                    "type": "price_update",
                    "data": price_updates,
                    "timestamp": datetime.utcnow().isoformat(),
                    "sequence": int(datetime.utcnow().timestamp())
                }
                
                # Broadcast to WebSocket clients and Redis
                await manager.broadcast_json(message)
                await manager.publish_to_redis("price_updates", message)
                
                # Wait before next update
                await asyncio.sleep(2)  # Update every 2 seconds
                
            except Exception as e:
                logger.error(f"Error in price streaming: {e}")
                await asyncio.sleep(5)  # Wait longer on error


async def stream_pnl_updates():
    """Stream P&L updates."""
    logger.info("Starting P&L update stream...")
    
    while True:
        try:
            # In production, this would fetch real P&L from database
            # Mock P&L update with some variation
            import random
            base_pnl = 12345.67
            variation = random.uniform(-0.1, 0.1)  # ±10% variation
            
            pnl_data = {
                "account_id": "demo",
                "total_pnl": round(base_pnl * (1 + variation), 2),
                "unrealized_pnl": round(8900.12 * (1 + variation * 0.8), 2),
                "realized_pnl": round(3445.55 * (1 + variation * 0.2), 2),
                "portfolio_value": round(500000.00 * (1 + variation * 0.05), 2),
                "day_change": round(base_pnl * variation, 2),
                "day_change_pct": round(variation * 100, 2)
            }
            
            message = {
                "type": "pnl_update",
                "data": pnl_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await manager.broadcast_json(message)
            await manager.publish_to_redis("pnl_updates", message)
            
            # Update every 10 seconds
            await asyncio.sleep(10)
            
        except Exception as e:
            logger.error(f"Error in P&L streaming: {e}")
            await asyncio.sleep(15)


async def stream_risk_alerts():
    """Stream risk alerts when thresholds are breached."""
    logger.info("Starting risk alert stream...")
    
    alert_counter = 0
    
    while True:
        try:
            # Mock risk alert generation
            # In production, this would monitor actual risk metrics
            
            # Generate different types of alerts periodically
            await asyncio.sleep(120)  # Check every 2 minutes
            
            alert_types = [
                {
                    "alert_type": "var_threshold",
                    "severity": "medium",
                    "message": "Portfolio VaR exceeded 95% confidence threshold",
                    "current_var": 1250000,
                    "threshold": 1000000,
                    "breach_percentage": 25.0
                },
                {
                    "alert_type": "concentration_risk", 
                    "severity": "high",
                    "message": "Single position exceeds 15% portfolio concentration limit",
                    "position": "TSLA",
                    "current_concentration": 18.5,
                    "limit": 15.0
                },
                {
                    "alert_type": "volatility_spike",
                    "severity": "low", 
                    "message": "Portfolio volatility increased by 30% vs 30-day average",
                    "current_vol": 0.045,
                    "avg_vol": 0.035,
                    "spike_percentage": 28.6
                }
            ]
            
            # Randomly select an alert type
            import random
            if random.random() < 0.3:  # 30% chance of alert
                alert_data = random.choice(alert_types)
                alert_data.update({
                    "account_id": "demo",
                    "alert_id": f"ALERT_{alert_counter:04d}",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                message = {
                    "type": "risk_alert",
                    "data": alert_data,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await manager.broadcast_json(message)
                await manager.publish_to_redis("risk_alerts", message)
                
                alert_counter += 1
                logger.info(f"Generated risk alert: {alert_data['alert_type']}")
            
        except Exception as e:
            logger.error(f"Error in risk alert streaming: {e}")
            await asyncio.sleep(30)


async def stream_market_status():
    """Stream market status updates."""
    logger.info("Starting market status stream...")
    
    while True:
        try:
            # Mock market status (would fetch from real market data)
            now = datetime.utcnow()
            
            # Simple market hours logic (US Eastern Time approximation)
            hour = now.hour
            is_market_open = 14 <= hour <= 21  # Rough US market hours in UTC
            
            status_data = {
                "market_status": "open" if is_market_open else "closed",
                "trading_session": "regular" if is_market_open else "after_hours",
                "next_open": "2024-01-01T14:30:00Z",  # Mock next open
                "server_time": now.isoformat(),
                "data_quality": "good",
                "feed_status": {
                    "prices": "active",
                    "trades": "active", 
                    "risk": "active"
                }
            }
            
            message = {
                "type": "market_status",
                "data": status_data,
                "timestamp": now.isoformat()
            }
            
            await manager.broadcast_json(message)
            await manager.publish_to_redis("market_status", message)
            
            # Update every 5 minutes
            await asyncio.sleep(300)
            
        except Exception as e:
            logger.error(f"Error in market status streaming: {e}")
            await asyncio.sleep(60)


# Background task management
_streaming_tasks: List[asyncio.Task] = []
_streaming_started = False


async def start_streaming_tasks():
    """Start all streaming background tasks."""
    global _streaming_tasks, _streaming_started
    
    if _streaming_started:
        return
    
    logger.info("Starting all streaming background tasks...")
    
    tasks = [
        asyncio.create_task(stream_price_updates()),
        asyncio.create_task(stream_pnl_updates()),
        asyncio.create_task(stream_risk_alerts()),
        asyncio.create_task(stream_market_status())
    ]
    
    _streaming_tasks.extend(tasks)
    _streaming_started = True
    
    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        logger.error(f"Streaming tasks error: {e}")
        _streaming_started = False


async def stop_streaming_tasks():
    """Stop all streaming background tasks."""
    global _streaming_tasks, _streaming_started
    
    logger.info("Stopping streaming background tasks...")
    
    for task in _streaming_tasks:
        if not task.done():
            task.cancel()
    
    # Wait for tasks to complete
    if _streaming_tasks:
        await asyncio.gather(*_streaming_tasks, return_exceptions=True)
    
    _streaming_tasks.clear()
    _streaming_started = False


async def initialize_streaming():
    """Initialize background streaming tasks."""
    logger.info("Initializing WebSocket streaming service...")
    
    # Start streaming tasks in background
    asyncio.create_task(start_streaming_tasks())


# Health check for streaming service
async def get_streaming_health():
    """Get health status of streaming service."""
    return {
        "status": "healthy" if _streaming_started else "stopped",
        "active_connections": len(manager.active_connections),
        "active_tasks": len([t for t in _streaming_tasks if not t.done()]),
        "redis_connected": manager.redis_client is not None,
        "subscriptions": {
            channel: len(subscribers) 
            for channel, subscribers in manager.subscriptions.items()
        }
    }