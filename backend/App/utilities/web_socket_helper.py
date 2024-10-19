# app/utilities/websocket_helpers.py

from fastapi import WebSocket, WebSocketDisconnect

async def stream_data_to_client(websocket: WebSocket, session_id: str, data: dict):
    """Function to stream new data to the WebSocket client."""
    try:
        await websocket.send_json(data)
        # print(f"Sent new data to session {session_id}: {data}")

    except WebSocketDisconnect:
        print(f"Session {session_id} disconnected while streaming.")
    except Exception as e:
        print(f"Error while sending data to session {session_id}: {e}")
