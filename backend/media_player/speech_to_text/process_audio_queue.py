import os
import glob
import threading
from collections import deque
import time
import whisperx
import whisper
from pyannote.audio import Pipeline, Model, Inference
from dotenv import load_dotenv
from pyannote.core import Segment
import numpy as np
from scipy.spatial.distance import cosine


load_dotenv()

speaker_diarization = os.getenv("speaker_diarization")
pipeline = os.getenv("pipeline")
inference_model = os.getenv("inference_model")

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
EMBEDDING_DIR = os.path.join(BASE_DIR, 'speech_to_text', 'embedding_data')
TEMP_DIR = os.path.join(BASE_DIR, 'speech_to_text', 'temp_audio_files') 

class ProcessAudioQueue:
    def __init__(self, temp_dir='temp_audio_files', session_id=None, device = None, model=None, audio_player=None):
        print("ProcessAudioQueue init: ", session_id)
        self.session_id = session_id
        self.queue = deque()
        self.device = device
        self.model = model
        self.whisper_model = whisper.load_model("base.en")
        self.pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1",
                        use_auth_token=pipeline)
        self.inference_model = Model.from_pretrained("pyannote/embedding", 
                        use_auth_token=inference_model)
        self.diarize_bank = {}

        self.stop_flag = False  # Flag to stop the thread
        self.monitor_thread = None  # Initialize the thread as None

        self.audio_player = audio_player
        self.audio_player.set_start_time_callback(self.on_start_time_change)
        self.cur_time = 0
        
        self._start_monitoring()


    def _start_monitoring(self):
        """
        Start the background thread to monitor the queue for files to process.
        """
        if not self.monitor_thread or not self.monitor_thread.is_alive():
            self.monitor_thread = threading.Thread(target=self._monitor_queue)
            self.monitor_thread.start()

    def _monitor_queue(self):
        """
        Continuously monitors the queue for files to process.
        """
        print(f"Started monitoring for session: {self.session_id}")
        while not self.stop_flag:
            if self.queue:
                self.dequeue()
            time.sleep(2)  # Wait for the defined interval before checking again

    def stop_monitoring(self):
        """
        Stop the background monitoring of the queue.
        Ensure that all files are processed before stopping.
        """
        if self.monitor_thread:
            # Wait for all files to be processed before stopping
            while self.queue:
                self.dequeue()
            # After the queue is empty, stop monitoring
            self.stop_flag = True
            self.monitor_thread.join()
            print(f"Stopped monitoring for session: {self.session_id}")

    def clear_queue(self):
        """
        Clear the queue and delete all files associated with the session ID.
        This method is called only after the monitoring thread has finished processing all files.
        """
        while self.queue:
            file_name = self.queue.popleft()
            self._delete_file(file_name)
        print("Queue cleared and all session files deleted.")

    def enqueue(self, file_name):
        """
        Add a new file name to the queue.
        """
        self.queue.append(file_name)

    def dequeue(self):
        if self.queue:
            file_name = self.queue.popleft()
            full_path = os.path.join(TEMP_DIR, file_name)
            # if file_name and os.path.exists(full_path):
            #     try:
            #         # print(f"Processing file: {file_name}")
            #         # print(f'Queue: {self.queue}')
            #         self.process_file(file_name)
            #     except Exception as e:
            #         print(f"Error processing file {file_name}: {e}")
            #     finally:
            #         self._delete_file(file_name)
            # else:
            #     print(f"File {file_name} no longer exists, skipping.")


    def process_file(self, file_name):
        """
        Process the file before deleting it.
        Custom processing logic can be implemented here.
        """
        try:
            full_path = os.path.join(TEMP_DIR, file_name)
            # print(f"Session ID: {self.session_id}, Processing file: {full_path}")
            self.embed_transcribe_speakers(full_path)
        except Exception as e:
            print(f'Queue: {self.queue}')
            print(f"Exception occurred while processing {file_name}: {e}")
            raise 

    def embed_transcribe_speakers(self, full_path):
        total_time = 0

        inference = Inference(self.inference_model, window="whole")
        audio = whisperx.load_audio(full_path)
        result = self.model.transcribe(audio, batch_size=16)
        align_model, metadata = whisperx.load_align_model(language_code="en", device=self.device)

        # # Align the transcription for word-level timing
        aligned_result = whisperx.align(result["segments"], align_model, metadata, full_path, self.device)
        diarize_model = whisperx.DiarizationPipeline(use_auth_token="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", device=self.device)
        diarize_segments = diarize_model(audio)
        aligned_result = whisperx.assign_word_speakers(diarize_segments, aligned_result)

        for segments in aligned_result["segments"]:
            phrases = {}
            for word in segments["words"]:
                if word["speaker"] not in phrases:
                    phrases[word["speaker"]] = {"text" : "", "start" : 0, "end" : 0, "speaker" : "", "session_id" : self.session_id}
                    phrases[word["speaker"]]["start"] = word["start"]
                phrases[word["speaker"]]["text"] += word["word"] + " "
                phrases[word["speaker"]]["end"] = word["end"]
            for phrase in phrases:
                segment = Segment(phrases[phrase]["start"], phrases[phrase]["end"])
                speaker_embedding = inference.crop(full_path, segment)
                similarities = self.recognize_speaker(speaker_embedding, phrases, phrase)
                speaker_similarity = max(similarities.values())
                speaker_name = max(similarities, key=similarities.get)

                if speaker_similarity < 0.1:
                    speaker_name = "Unknown"

                phrases[phrase]["speaker"] = speaker_name
                total_time = self.cur_time + phrases[phrase]["end"]
                self.diarize_bank[str(convert_seconds_to_hhmmss(total_time))] = phrases[phrase]
        self.cur_time = total_time
        print(f'Total time: ', convert_seconds_to_hhmmss(self.cur_time))
        # print(self.diarize_bank)


    def recognize_speaker(self, speaker_embedding, phrases, phrase):
        trump_embedding_path = os.path.join(EMBEDDING_DIR, 'trump_embedding.npy')
        trump_embedding = np.load(trump_embedding_path)
        kamala_embedding_path = os.path.join(EMBEDDING_DIR, 'kamala_embedding.npy')
        kamala_embedding = np.load(kamala_embedding_path)
        speaker = {"Trump" : 0, "Kamala" : 0}
        
        if speaker_embedding.ndim == 1:
            similarities = []
            for idx, trump_frame in enumerate(trump_embedding):
                similarity = 1 - cosine(speaker_embedding, trump_frame)
                similarities.append(similarity)
            mean_similarity = np.mean(similarities)
            speaker["Trump"] = mean_similarity

            similarities = []
            for idx, kamala_frame in enumerate(kamala_embedding):
                similarity = 1 - cosine(speaker_embedding, kamala_frame)
                similarities.append(similarity)
            mean_similarity = np.mean(similarities)
            speaker["Kamala"] = mean_similarity
            
            
            return speaker
        else:
            print(f"Speaker embedding is not 1D: {speaker_embedding.ndim}D")
            return None



    def _delete_file(self, file_name, max_retries=5, wait_time=0.5):
        """
        Delete the specified file from the file system, waiting until it is accessible.
        """

        # print(f"Deleting file: {file_name}")
        full_path = os.path.join(TEMP_DIR, file_name)

        retries = 0
        while retries < max_retries:
            try:
                if os.path.exists(full_path):
                    with open(full_path, 'r+'):
                        pass

                    os.remove(full_path)
                    return
                else:
                    print(f"File does not exist: {full_path}")
                    return
            except PermissionError:
                retries += 1
                print(f"PermissionError: File is in use. Retrying {retries}/{max_retries}...")
                time.sleep(wait_time)
            except FileNotFoundError:
                print(f"File not found during deletion: {full_path}")
                return
        print(f"Failed to delete file after {max_retries} attempts: {full_path}")


    def list_files(self):
        """
        List all files currently in the queue.
        """
        return list(self.queue)
    
    def on_start_time_change(self, new_time):
        """Handle the change in player's start time."""
        print(f"Player start time changed to: {new_time}")
        self.cur_time = new_time



def convert_seconds_to_hhmmss(seconds):
    """
    Convert seconds to hh:mm:ss.ms format.
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02}.{milliseconds:03}"

