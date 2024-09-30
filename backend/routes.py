# utils/routes.py
from fastapi import APIRouter, HTTPException, Request, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from urllib.parse import quote
import os
from utils.audio_player import AudioPlayer
from utils.convert_seconds import convert_seconds_to_hh_mm_ss
from session_middleware import get_session_id
from utils.process_audio_queue import ProcessAudioQueue, check_folder
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from typing import Dict
from threading import Event, Lock
import whisperx
import torch



router = APIRouter()

VIDEO_DIR = "videoclips"
audio_player = AudioPlayer()

# monitoring_event = Event()

# Dictionary to keep track of active threads for each session
active_threads: Dict[str, Observer] = {}
active_threads_lock = Lock()

device = "cpu"
model = whisperx.load_model("base", device, compute_type="float32")



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
        range_val = range_header.strip().split("=")[-1]
        range_start, range_end = range_val.split("-")
        range_start = int(range_start) if range_start else 0
        range_end = int(range_end) if range_end else file_size - 1
        content_length = range_end - range_start + 1
        headers = {
            "Content-Range": f"bytes {range_start}-{range_end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(content_length),
            "Content-Type": "video/mp4",
        }

        def iter_file():
            with open(video_path, 'rb') as video_file:
                video_file.seek(range_start)
                yield video_file.read(content_length)

        return StreamingResponse(iter_file(), status_code=206, headers=headers)
    else:
        headers = {
            "Content-Length": str(file_size),
            "Content-Type": "video/mp4",
            "Accept-Ranges": "bytes",
        }

        def iter_file():
            with open(video_path, 'rb') as video_file:
                yield from video_file

        return StreamingResponse(iter_file(), headers=headers)
    
class FileCreationHandler(FileSystemEventHandler):
    def __init__(self, session_id, device=None, model=None):
        super().__init__()
        self.device = device
        self.model = model
        self.audio_queue = ProcessAudioQueue(session_id=session_id, device=self.device, model=self.model)

    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith('.wav'):
            file_name = os.path.basename(event.src_path)
            # print(f"New file detected: {file_name} with start time: {start_time}")
            self.audio_queue.enqueue(file_name)
            self.audio_queue.dequeue()  # Process the file immediately
            
# Dictionary to keep track of active event handlers for each session
active_event_handlers: Dict[str, FileCreationHandler] = {}

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
        audio_player.set_session(session_id)
        event_handler = None

        if action == 'play':
            print(action, convert_seconds_to_hh_mm_ss(time))
            audio_player.play(audio_path, time)

            with active_threads_lock:
                # Stop the existing thread if it exists
                if session_id in active_threads:
                    active_threads[session_id].stop()
                    active_threads[session_id].join()
                
                # Start a new thread for folder monitoring
                event_handler = FileCreationHandler(session_id, device, model)
                observer = Observer()
                observer.schedule(event_handler, path='temp_audio_files', recursive=False)
                observer.start()

                # Store the observer and event handler for this session
                active_threads[session_id] = observer
                active_event_handlers[session_id] = event_handler

        elif action == 'pause':
            print(action, convert_seconds_to_hh_mm_ss(time))
            audio_player.pause()

            # # Retrieve the existing event handler for the session and clear its queue
            # if session_id in active_event_handlers:
            #     event_handler = active_event_handlers[session_id]
            #     event_handler.audio_queue.clear_queue()  # Clear the queue
            # else:
            #     print(f"No active event handler found for session: {session_id}")

    except Exception as e:
        print(f"Error processing audio control command: {e}")

    return {"status": "ok"}


