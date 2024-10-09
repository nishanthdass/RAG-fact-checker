from fastapi import APIRouter, HTTPException, Request, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect
from app.utilities.stream_response import handle_full_request, handle_range_request
from urllib.parse import quote
import os
from media_player.audio_player import AudioPlayer
from app.session_middleware import get_session_id
from app.session_manager_init import session_manager
from media_player.speech_to_text.process_audio_queue import ProcessAudioQueue
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from typing import Dict
from threading import Lock
import whisperx

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
VIDEO_DIR = os.path.join(BASE_DIR, 'media_player', 'video_clips')
TEMP_AUDIO_DIR = os.path.join(BASE_DIR, 'media_player', 'speech_to_text', 'temp_audio_files')

# audio_player = AudioPlayer(temp_dir=TEMP_AUDIO_DIR)

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    # Generate a session ID when the WebSocket connection is established
    session_id = session_manager.create_session()
    
    # Send the session ID back to the client
    print(f"Session {session_id} connected.")
    await websocket.send_text(f"session_id:{session_id}")

    try:
        while True:
            data = await websocket.receive_text()
            # Handle data or messages from the client
            print(f"Received data from session {session_id}: {data}")
    except WebSocketDisconnect:
        # Clean up session when WebSocket disconnects
        print(f"Session {session_id} disconnected.")
        session_manager.delete_session(session_id)

@router.get("/videos")
async def get_videos():
    try:
        files = os.listdir(VIDEO_DIR)
        video_files = [
            {"name": file, "url": f"http://localhost:8000/videos/{quote(file)}"}
            for file in files
            if file.endswith((".mp4", ".webm"))  # Filter by video file types
        ]
        return video_files
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/videos/{video_name}")
async def get_video(video_name: str, request: Request):
    video_path = os.path.join(VIDEO_DIR, video_name)
    
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video not found")

    file_size = os.path.getsize(video_path)
    range_header = request.headers.get('range')

    if range_header:
        return handle_range_request(video_path, file_size, range_header)
    else:
        return handle_full_request(video_path, file_size)
    

@router.post("/audio-control")
async def control_audio(request: Request, background_tasks: BackgroundTasks, session_id: str = Depends(get_session_id)):
    data = await request.json()
    action = data.get('action')
    time = data.get('time')
    video_name = data.get('videoName')

    audio_path = os.path.join(VIDEO_DIR, video_name)
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio not found")

    try:
        audio_player = session_manager.get_session(session_id)["audio_player"]

        if action == 'play':
            audio_player.play(audio_path, time)
            print("playing audio: ", time)
        elif action == 'pause':
            audio_player.pause()

    except Exception as e:
        print(f"Error processing audio control command: {e}")

    return {"status": "ok"}

