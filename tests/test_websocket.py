"""
Simple test script to verify WebSocket functionality.
"""
import asyncio
import json
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_websocket():
    """Test WebSocket connection and message sending."""
    
    uri = "ws://localhost:8000/ws?user_id=test_user&chat_id=test_chat&client_id=test_client"
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("Connected to WebSocket")
            
            # Send a ping message
            ping_message = {
                "type": "ping",
                "event": "test",
                "data": {"message": "ping"}
            }
            
            await websocket.send(json.dumps(ping_message))
            logger.info("Sent ping message")
            
            # Send a chat message
            chat_message = {
                "type": "chat",
                "event": "send_message",
                "data": {
                    "message": "Hello from test client!",
                    "target_chat_id": "test_chat"
                }
            }
            
            await websocket.send(json.dumps(chat_message))
            logger.info("Sent chat message")
            
            # Listen for responses
            try:
                while True:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(response)
                    logger.info(f"Received: {data}")
                    
                    # Break after receiving a few messages
                    if data.get("type") == "pong":
                        break
                        
            except asyncio.TimeoutError:
                logger.info("No more messages received")
            
    except Exception as e:
        logger.error(f"WebSocket test error: {e}")


async def test_multiple_connections():
    """Test multiple WebSocket connections."""
    
    async def create_connection(user_id: str, chat_id: str):
        uri = f"ws://localhost:8000/ws?user_id={user_id}&chat_id={chat_id}"
        
        try:
            async with websockets.connect(uri) as websocket:
                logger.info(f"Connected user {user_id}")
                
                # Send a message
                message = {
                    "type": "chat",
                    "event": "send_message", 
                    "data": {
                        "message": f"Hello from {user_id}!",
                        "target_chat_id": chat_id
                    }
                }
                
                await websocket.send(json.dumps(message))
                
                # Listen for a short time
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    data = json.loads(response)
                    logger.info(f"User {user_id} received: {data}")
                except asyncio.TimeoutError:
                    pass
                    
        except Exception as e:
            logger.error(f"Connection error for {user_id}: {e}")
    
    # Create multiple connections
    tasks = [
        create_connection("user1", "chat1"),
        create_connection("user2", "chat1"),
        create_connection("user3", "chat2"),
    ]
    
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    print("Testing WebSocket functionality...")
    print("Make sure the bot is running on localhost:8000")
    
    # Test single connection
    print("\n=== Testing single connection ===")
    asyncio.run(test_websocket())
    
    # Test multiple connections
    print("\n=== Testing multiple connections ===")
    asyncio.run(test_multiple_connections())
    
    print("\nWebSocket tests completed!")
