import os
import uuid
from fastapi import Request, HTTPException
from typing import Optional, Dict
from app.utilities.file_creation_handler import FileCreationHandler
from media_player.speech_to_text.process_audio_queue import ProcessAudioQueue
import whisperx
from watchdog.observers import Observer
from typing import Dict
from threading import Lock
from media_player.audio_player import AudioPlayer

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
TEMP_AUDIO_DIR = os.path.join(BASE_DIR, 'media_player', 'speech_to_text', 'temp_audio_files')

print(TEMP_AUDIO_DIR)

device = "cpu"
model = whisperx.load_model("base", device, compute_type="float32")


class SessionManager:
    def __init__(self):
        # Dictionary to store active sessions in-memory
        self.active_sessions: Dict[str, dict] = {}
        self.active_threads: Dict[str, Observer] = {}
        self.active_threads_lock = Lock()

    def create_session(self) -> str:
        """Generate a new session ID and store it in active_sessions."""
        session_id = str(uuid.uuid4())
        audio_player = AudioPlayer(temp_dir=TEMP_AUDIO_DIR)
        audio_player.set_session(session_id)
        
        # Create ProcessAudioQueue
        audio_queue = ProcessAudioQueue(session_id=session_id, device=device, model=model)
        
        
        self.active_sessions[session_id] = {
            "events": None,  # Reference to the observer thread
            "audio_player": audio_player,
            "audio_queue": audio_queue,  # Store reference to ProcessAudioQueue
        }
        print("sessions: ", self.active_sessions.keys())

        # Start observing file creations
        self.handle_file_created(session_id, device, model)

        return session_id

    def get_session(self, session_id: str) -> Optional[dict]:
        """Retrieve session data based on the session ID."""
        session_data = self.active_sessions.get(session_id)
        if session_data:
            print(f"Retrieved session: {session_id}")
            return session_data
        print(f"Session not found: {session_id}")
        return None

    def delete_session(self, session_id: str) -> bool:
        """Delete a session by session ID."""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            print(f"Deleted session: {session_id}")
            return True
        print(f"Session not found: {session_id}")
        return False

    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        return session_id in self.active_sessions

    def cleanup_sessions(self):
        """Remove expired or inactive sessions."""
        # Implement logic to clean up old or inactive sessions as needed.
        pass

    def handle_file_created(self, session_id: str, device: str, model: str):
        print("Handling file created" , session_id)
        with self.active_threads_lock:
            if session_id in self.active_threads:
                self.active_threads[session_id].stop()
                self.active_threads[session_id].join()
            audio_queue = self.active_sessions[session_id]["audio_queue"]
            event_handler = FileCreationHandler(audio_queue)
            observer = Observer()
            observer.schedule(event_handler, path=TEMP_AUDIO_DIR, recursive=False)
            observer.start()
            self.active_threads[session_id] = observer
            self.active_sessions[session_id]["events"] = self.active_threads[session_id]

        print("threads: ", self.active_threads.keys())


    def delete_session(self, session_id: str) -> bool:
        """Delete a session by session ID and clean up its resources."""
        session_data = self.active_sessions.get(session_id)
        if session_data:
            # Stop the observer
            observer = session_data["events"]
            observer.stop()
            observer.join()

            # Stop the audio player
            audio_player = session_data["audio_player"]
            audio_player.stop()

            # Stop the ProcessAudioQueue monitoring thread
            audio_queue = session_data["audio_queue"]
            audio_queue.stop_monitoring()
            audio_queue.clear_queue()

            # Remove session from active sessions
            del self.active_sessions[session_id]
            print(f"Deleted session: {session_id}")
            return True
        print(f"Session not found: {session_id}")
        return False
