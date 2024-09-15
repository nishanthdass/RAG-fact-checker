import os
import glob
import shutil
from collections import deque
import time

class ProcessAudioQueue:
    def __init__(self, temp_dir='temp_audio_files', session_id=None):
        self.session_id = session_id
        self.temp_dir = temp_dir
        self.queue = deque()

        # Load all files in the temp directory associated with the session ID
        self._load_files()

    def _load_files(self):
        """
        Load all files from the temporary directory that match the session ID
        and add their names to the queue.
        """
        session_prefix = f"{self.session_id}_"
        # Get full paths of matching files
        files = sorted(glob.glob(os.path.join(self.temp_dir, f"{session_prefix}*.wav")))
        # Extract file names from paths
        file_names = [os.path.basename(f) for f in files]
        self.queue.extend(file_names)
        print(f"Loaded files into queue: {self.queue}")

    def enqueue(self, file_name):
        """
        Add a new file name to the queue.
        """
        self.queue.append(file_name)

    def dequeue(self):
        """
        Process the first file in the queue, then remove it.
        """
        if self.queue:
            file_name = self.queue.popleft()
            if file_name:
                self.process_file(file_name)
                self._delete_file(file_name)
        else:
            print("Queue is empty.")

    def process_file(self, file_name):
        """
        Process the file before deleting it.
        Custom processing logic can be implemented here.
        """
        full_path = os.path.join(self.temp_dir, file_name)
        print(f"Processing file: {full_path}")
        # Add custom processing logic here (e.g., analyze audio, convert format)

    def _delete_file(self, file_name, max_retries=5, wait_time=0.5):
        """
        Delete the specified file from the file system, waiting until it is accessible.
        """
        full_path = os.path.join(self.temp_dir, file_name)
        retries = 0
        while retries < max_retries:
            try:
                if os.path.exists(full_path):
                    # Attempt to open the file to ensure it is not being used
                    with open(full_path, 'r+'):
                        pass  # File is accessible, proceed to delete

                    os.remove(full_path)
                    print(f"Deleted file: {full_path}")
                    return  # Exit after successful deletion
                else:
                    print(f"File does not exist: {full_path}")
                    return
            except PermissionError:
                retries += 1
                print(f"PermissionError: File is in use. Retrying {retries}/{max_retries}...")
                # Wait before retrying to give the process some time to release the file
                time.sleep(wait_time)
            except FileNotFoundError:
                print(f"File not found during deletion: {full_path}")
                return

        # If all retries fail
        print(f"Failed to delete file after {max_retries} attempts: {full_path}")

    def clear_queue(self):
        """
        Clear the queue and delete all files associated with the session ID.
        """
        while self.queue:
            file_name = self.queue.popleft()
            self._delete_file(file_name)
        print("Queue cleared and all session files deleted.")

    def list_files(self):
        """
        List all files currently in the queue.
        """
        return list(self.queue)

def check_folder(session_id):
    temp_dir = 'temp_audio_files'
    audio_queue = ProcessAudioQueue(temp_dir=temp_dir, session_id=session_id)
    
    # List files currently in the queue
    files = audio_queue.list_files()
    print(f"Files in queue: {files}")
