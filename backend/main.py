"""
WebSocket server that connects frontend to backend components.
This file is purely glue code - no business logic here.
Routes messages between React frontend and Python AI/Model backend.
"""

import asyncio
import json
import websockets
import logging
from datetime import datetime
from typing import Set, Dict, Any

# Simple flat imports - all files in backend folder
from agent import ForecastAgent
from model import ForecastModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ForecastServer:
    def __init__(self):
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.agent = ForecastAgent()
        self.forecast_model = ForecastModel()
        # Single shared forecast state for all clients
        self.current_forecast = None
        self.modifications = []
        
    async def initialize(self):
        """Initialize the server with static forecast data"""
        logger.info("Initializing forecast server...")
        # Generate forecast once at startup using RNN
        self.current_forecast = self.forecast_model.generate_forecast()
        logger.info(f"Server initialized with {len(self.current_forecast)} hours of forecast data")
        
    async def register_client(self, websocket):
        """Register a new client connection"""
        self.clients.add(websocket)
        logger.info(f"Client connected. Total clients: {len(self.clients)}")
        
        # Send current forecast state to new client
        await websocket.send(json.dumps({
            "type": "initial_data",
            "data": {
                "forecast": self.current_forecast,
                "modifications": self.modifications,
                "timestamp": datetime.now().isoformat()
            }
        }))
        
    async def unregister_client(self, websocket):
        """Remove a client connection"""
        self.clients.remove(websocket)
        logger.info(f"Client disconnected. Total clients: {len(self.clients)}")
        
    async def broadcast_update(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients"""
        if self.clients:
            message_str = json.dumps(message)
            await asyncio.gather(
                *[client.send(message_str) for client in self.clients],
                return_exceptions=True
            )
            
    async def handle_message(self, websocket, message_str: str):
        """Handle incoming messages from clients"""
        try:
            message = json.loads(message_str)
            message_type = message.get("type")
            
            if message_type == "chat_message":
                # Process through agent
                user_message = message.get("data", {}).get("message", "")
                response = self.agent.process_message(
                    user_message, 
                    self.current_forecast
                )
                
                # Send agent response
                await websocket.send(json.dumps({
                    "type": "agent_response",
                    "data": {
                        "response": response["response"],
                        "modifications": response.get("modifications", [])
                    }
                }))
                
                # Apply modifications immediately if any
                if response.get("modifications"):
                    await self.apply_modifications(response["modifications"])
                    
            elif message_type == "clear_modifications":
                # Reset to original RNN forecast
                self.modifications = []
                self.current_forecast = self.forecast_model.generate_forecast()
                await self.broadcast_update({
                    "type": "forecast_update",
                    "data": {
                        "forecast": self.current_forecast,
                        "modifications": [],
                        "timestamp": datetime.now().isoformat()
                    }
                })
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {message_str}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            
    async def apply_modifications(self, new_modifications):
        """Apply modifications directly to the current forecast and broadcast update"""
        # Store modifications for display
        self.modifications.extend(new_modifications)
        
        # Apply modifications directly to current forecast
        for mod in new_modifications:
            metric = mod.get("metric")
            mod_type = mod.get("type")
            value = mod.get("value")
            start_date = mod.get("start_date")
            end_date = mod.get("end_date")
            
            # Convert dates if needed
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            # Apply to each hour in the forecast
            for item in self.current_forecast:
                item_date = datetime.fromisoformat(item['date']).date()
                
                if start_date <= item_date <= end_date and metric in item:
                    current_value = item[metric]
                    
                    if mod_type == 'percentage':
                        new_value = current_value * (1 + value / 100)
                    elif mod_type == 'absolute':
                        new_value = current_value + value
                    elif mod_type == 'set':
                        new_value = value
                    else:
                        continue
                    
                    # Apply bounds
                    if metric == 'rooms':
                        new_value = max(0, min(99, new_value))
                    else:
                        new_value = max(0, new_value)
                    
                    item[metric] = float(new_value) if metric == 'rooms' else int(new_value)
        
        # Broadcast updated forecast to all clients
        await self.broadcast_update({
            "type": "forecast_update",
            "data": {
                "forecast": self.current_forecast,
                "modifications": self.modifications,
                "timestamp": datetime.now().isoformat()
            }
        })
        
    async def handle_connection(self, websocket, path):
        """Handle a client WebSocket connection"""
        await self.register_client(websocket)
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister_client(websocket)
            
    async def start_server(self, host="0.0.0.0", port=8567):
        """Start the WebSocket server"""
        await self.initialize()
        logger.info(f"Starting WebSocket server on {host}:{port}")
        async with websockets.serve(self.handle_connection, host, port):
            await asyncio.Future()  # Run forever

# Main entry point
async def main():
    server = ForecastServer()
    await server.start_server()

if __name__ == "__main__":
    asyncio.run(main())