import os
from watchdog.events import FileSystemEventHandler
from media_player.speech_to_text.process_audio_queue import ProcessAudioQueue

class FileCreationHandler(FileSystemEventHandler):
    def __init__(self, audio_queue, session_id):
        super().__init__()
        self.audio_queue = audio_queue
        self.session_id = session_id

    def on_created(self, event):
        # print(f"File created: {event.src_path}")
        if event.is_directory:
            return
        if event.src_path.endswith('.wav'):
            file_name = os.path.basename(event.src_path)
            # Only process files that contain the session_id in the file name
            if self.session_id in file_name:
                # print(f"Processing file: {file_name} for session: {self.session_id}")
                self.audio_queue.enqueue(file_name)
            else:
                print(f"Ignoring file: {file_name} as it does not match session: {self.session_id}")

    def cleanup(self):
        """Cleanup resources managed by this handler."""
        self.audio_queue.stop_monitoring()
