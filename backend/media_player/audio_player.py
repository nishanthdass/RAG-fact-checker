import numpy as np
import threading
import subprocess
import pyaudio
import time
import wave
import uuid
import os
from media_player.speech_to_text.process_audio_queue import ProcessAudioQueue
import webrtcvad

class AudioPlayer:
    def __init__(self, temp_dir='temp_audio_files'):
        self.session = None
        self.process = None
        self.stream = None
        self.lock = threading.Lock()
        self.terminate = False
        self.thread = None
        self.file_count = 0
        self.time_file_dict = {}

        script_dir = os.path.dirname(os.path.abspath(__file__))
        print(script_dir)
        print(temp_dir)
        self.temp_dir = os.path.join(script_dir, temp_dir)
        print(self.temp_dir)
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

    def play(self, audio_path, start_time=0):
        self.thread = threading.Thread(target=self._play_in_thread, args=(audio_path, start_time), daemon=True)
        self.thread.start()

    def _play_in_thread(self, audio_path, start_time):

        sample_rate = 16000  # Hz
        channels = 1  # Mono
        sample_width = 2  # Bytes for 16-bit PCM

        frame_duration_ms = 20  # VAD frame duration in milliseconds
        frame_samples = int(sample_rate * frame_duration_ms / 1000)
        frame_size = frame_samples * sample_width * channels  # VAD frame size in bytes

        vad_buffer = b''  # Buffer to accumulate data for VAD

        command = [
            "ffmpeg",
            "-ss", str(start_time),
            "-i", audio_path,
            "-f", "s16le",  # Raw PCM data
            "-acodec", "pcm_s16le",
            "-ac", "1",  # Mono
            "-ar", str(sample_rate),  # Use the supported sample rate
            "-",
        ]

        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p = pyaudio.PyAudio()
        vad = webrtcvad.Vad()
        vad.set_mode(3)

        silence_duration = 0
        max_silence_duration = 0.1  # Seconds
        max_chunk_duration = 5  # Seconds
        min_chunk_duration = 3  # Seconds
        current_chunk_duration = 0
        isStart = False
        current_chunk_buffer = b'' 
        elapsed_time = 0.0  # Initialize elapsed_time
        clip_start_time = None
        def callback(in_data, frame_count, time_info, status):
            nonlocal silence_duration, current_chunk_duration, vad_buffer, isStart, current_chunk_buffer, clip_start_time, elapsed_time
            
            requested_bytes = frame_count * sample_width * channels
            audio_data = process.stdout.read(requested_bytes)
            
            if not audio_data or self.terminate:
                return (None, pyaudio.paComplete)
            
            vad_buffer += audio_data

            while len(vad_buffer) >= frame_size:
                vad_frame = vad_buffer[:frame_size]
                vad_buffer = vad_buffer[frame_size:]
                elapsed_time += frame_duration_ms / 1000
                try:
                    is_speech = vad.is_speech(vad_frame, sample_rate)

                    if not isStart:
                        isStart = True
                        silence_duration = 0
                        current_chunk_duration = frame_duration_ms / 1000
                        current_chunk_buffer = vad_frame
                        clip_start_time = start_time + elapsed_time - (frame_duration_ms / 1000.0)

                    elif isStart:
                        current_chunk_duration += frame_duration_ms / 1000
                        if not is_speech:
                            silence_duration += frame_duration_ms / 1000
                            if silence_duration >= max_silence_duration and (
                                min_chunk_duration <= current_chunk_duration <= max_chunk_duration
                                or current_chunk_duration >= max_chunk_duration
                            ):
                                session_prefix = f"{self.session}_" if self.session else ""
                                file_name = os.path.join(
                                    self.temp_dir, f"{session_prefix}temp_audio_{self.file_count}.wav"
                                )
                                chunk_audio_data_np = np.frombuffer(current_chunk_buffer, dtype=np.int16)
                                self._save_clip(file_name, chunk_audio_data_np, sample_rate, channels, sample_width)
                                # print(f"Saving clip to {file_name} starting at {clip_start_time} seconds")
                                self.time_file_dict[file_name] = clip_start_time
                                current_chunk_buffer = b''
                                isStart = False
                                current_chunk_duration = 0
                                silence_duration = 0
                                self.file_count += 1
                        else:
                            silence_duration = 0
                        current_chunk_buffer += vad_frame

                except Exception as e:
                    print(f"Error in vad.is_speech: {e}")
                    return (None, pyaudio.paAbort)
                
            return (audio_data, pyaudio.paContinue)

        stream = p.open(format=pyaudio.paInt16,  # 16-bit PCM
                        channels=channels,       
                        rate=sample_rate,        
                        output=True,
                        stream_callback=callback)
       
        with self.lock:
            self.process = process
            self.stream = stream
            self.terminate = False

        stream.start_stream()

        try:
            while not self.terminate and stream.is_active():
                time.sleep(0.1)
        finally:
            self.stop()
            self._save_remaining_chunk(current_chunk_buffer, sample_rate, channels, sample_width)

    def _save_remaining_chunk(self, current_chunk_buffer, sample_rate, channels, sample_width):
        """ Save the last chunk if it's non-empty """
        if current_chunk_buffer:
            session_prefix = f"{self.session}_" if self.session else ""
            file_name = os.path.join(self.temp_dir, f"{session_prefix}temp_audio_{self.file_count}.wav")
            chunk_audio_data_np = np.frombuffer(current_chunk_buffer, dtype=np.int16)
            self._save_clip(file_name, chunk_audio_data_np, sample_rate, channels, sample_width)
            self.time_file_dict[file_name] = time.time()  # Approximate time if needed
            self.file_count += 1

    def _save_clip(self, file_name, audio_data, sample_rate, channels, sample_width):
        with wave.open(file_name, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_data.tobytes())

    def stop(self):
        with self.lock:
            self.terminate = True
            if self.stream:
                try:
                    if self.stream.is_active():
                        # print("Stopping the stream...")
                        self.stream.stop_stream()
                except Exception as e:
                    print(f"Error stopping the stream: {e}")

                try:
                    # print("Closing the stream...")
                    self.stream.close()
                except Exception as e:
                    print(f"Error closing the stream: {e}")

            self.stream = None

            if self.process:
                try:
                    # print("Killing the process...")
                    self.process.kill()
                    self.process.wait()
                except Exception as e:
                    print(f"Error killing the process: {e}")

            self.process = None
            # print("Audio resources have been cleaned up.")

    def pause(self):
        self.stop()

    def set_session(self, session):
        self.session = session

    def get_clip_start_time(self, file_name):
        if file_name in self.time_file_dict:
            return self.time_file_dict[file_name]
        else:
            return None


            

