import os
from watchdog.events import FileSystemEventHandler
from media_player.speech_to_text.process_audio_queue import ProcessAudioQueue

class FileCreationHandler(FileSystemEventHandler):
    def __init__(self, audio_queue):
        super().__init__()

        self.audio_queue = audio_queue

    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith('.wav'):
            file_name = os.path.basename(event.src_path)
            self.audio_queue._load_files()

    def cleanup(self):
        """Cleanup resources managed by this handler."""
        self.audio_queue.stop_monitoring()