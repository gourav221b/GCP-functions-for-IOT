import os
import asyncio
import websockets
import json
from google.cloud import pubsub_v1

# Pub/Sub setup
PROJECT_ID = os.environ.get('GCP_PROJECT_ID')
SUBSCRIPTION_ID = 'rectangle-commands-sub'  # update this with the subscription id you create
subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)

CONNECTIONS = set()

async def register_client(websocket):
    """Registers a new WebSocket connection."""
    CONNECTIONS.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        CONNECTIONS.remove(websocket)

async def consume_pubsub():
    """Pulls messages from Pub/Sub and broadcasts them to all clients."""
    while True:
        response = subscriber.pull(
            request={"subscription": subscription_path, "max_messages": 10}
        )
        for received_message in response.received_messages:
            data = received_message.message.data.decode("utf-8")
            # Broadcast the message to all connected clients
            if CONNECTIONS:
                await asyncio.gather(*[ws.send(data) for ws in CONNECTIONS])
            subscriber.acknowledge(
                request={"subscription": subscription_path, "ack_ids": [received_message.ack_id]}
            )
        await asyncio.sleep(1) # Wait 1 second before polling again

async def main():
    """Starts the WebSocket server and Pub/Sub consumer."""
    async with websockets.serve(register_client, "0.0.0.0", 8080):
        await consume_pubsub()

if __name__ == "__main__":
    asyncio.run(main())
