import numpy as np
import threading
import subprocess
import pyaudio
import time
import wave
import os
import webrtcvad
from media_player.speech_to_text.process_audio_queue import convert_seconds_to_hhmmss
import asyncio



class AudioPlayer:
    def __init__(self, temp_dir='temp_audio_files'):
        self.session = None
        self.start_time = 0
        self.process = None
        self.stream = None
        self.lock = threading.Lock()
        self.terminate = False
        self.thread = None
        self.file_count = 0
        self.time_file_dict = {}
        # self.playing_event = threading.Event()

        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.temp_dir = os.path.join(script_dir, temp_dir)
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

    def play(self, audio_path, start_time=0):
        # self.playing_event.clear() 
        self.thread = threading.Thread(target=self._play_in_thread, args=(audio_path, start_time), daemon=True)
        self.thread.start()

        if self.start_time != start_time and self.on_start_time_change:
            self.on_start_time_change(start_time)

        self.start_time = start_time
        # self.playing_event.set() 

    def set_start_time_callback(self, callback):
        """Set a callback to be triggered when start time changes."""
        self.on_start_time_change = callback

    def pad_audio_frame(frame, target_size):
        """Pad the frame with zeros (silence) to match the target size."""
        pad_length = target_size - len(frame)
        if pad_length > 0:
            frame += b'\x00' * pad_length  # Pad with silence (zeros)
        return frame
    

    def _play_in_thread(self, audio_path, start_time):
        sample_rate = 48000  # Hz
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
        max_chunk_duration = 7  # Seconds
        min_chunk_duration = 5  # Seconds
        current_chunk_duration = 0
        current_chunk_buffer = b'' 
        elapsed_time = start_time
        clip_start_time = 0
        isStart = False  # Reintroducing the isStart flag
        
        def callback(in_data, frame_count, time_info, status):
            nonlocal silence_duration, current_chunk_duration, vad_buffer, current_chunk_buffer, elapsed_time, start_time, clip_start_time, isStart
            
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

                    if not isStart and is_speech:
                        # Only start capturing the chunk when speech is detected
                        isStart = True
                        silence_duration = 0
                        current_chunk_buffer = vad_frame  # Start new buffer with current frame
                        clip_start_time = elapsed_time
                    elif isStart:
                        current_chunk_duration += frame_duration_ms / 1000
                        if current_chunk_duration >= max_chunk_duration:
                            # Save the completed audio chunk
                            self._save_audio_chunk(current_chunk_buffer, sample_rate, channels, sample_width, elapsed_time, clip_start_time)
                            current_chunk_buffer = b''
                            isStart = False  # Reset for the next chunk
                            current_chunk_duration = 0
                        if not is_speech:
                            silence_duration += frame_duration_ms / 1000
                            if silence_duration >= max_silence_duration and (
                                min_chunk_duration <= current_chunk_duration
                            ):
                                # Save the completed audio chunk
                                self._save_audio_chunk(current_chunk_buffer, sample_rate, channels, sample_width, elapsed_time, clip_start_time)
                                current_chunk_buffer = b''
                                isStart = False  # Reset for the next chunk
                                current_chunk_duration = 0
                                silence_duration = 0
                        else:
                            silence_duration = 0  # Reset silence when speech is detected
                        current_chunk_buffer += vad_frame

                except Exception as e:
                    print(f"Error in vad.is_speech: {e}")
                    return (None, pyaudio.paAbort)
                
            silent_data = b'\x00' * frame_size
            return (silent_data, pyaudio.paContinue)
        

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
            # Save the remaining audio chunk when the stream ends
            self._save_audio_chunk(current_chunk_buffer, sample_rate, channels, sample_width, elapsed_time, clip_start_time)


    def _save_audio_chunk(self, current_chunk_buffer, sample_rate, channels, sample_width, elapsed_time, clip_start_time):
        """ Save the current audio chunk, adding 1 second of silence at the end if it's non-empty. """
        if current_chunk_buffer:
            # Add 1 second of silence to the end of the chunk
            silence_samples = sample_rate * channels * sample_width  # Number of bytes for 1 second of silence
            silence = b'\x00' * silence_samples  # Create the silence buffer

            # Append silence to the current chunk buffer
            padded_chunk = silence + current_chunk_buffer + silence

            chunk_audio_data_np = np.frombuffer(padded_chunk, dtype=np.int16)
            session_prefix = f"{self.session}_" if self.session else ""
            file_label = f"{session_prefix}temp_audio_{self.file_count}.wav"
            file_name = os.path.join(self.temp_dir, f"{session_prefix}temp_audio_{self.file_count}.wav")
            print({"start": clip_start_time, "end": elapsed_time})
            self.time_file_dict[file_label] = {"start": clip_start_time, "end": elapsed_time}  # Adding 1 second to the end time
            self._save_clip(file_name, chunk_audio_data_np, sample_rate, channels, sample_width)
            self.file_count += 1


    def _save_clip(self, file_name, audio_data, sample_rate, channels, sample_width):
        with wave.open(file_name, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_data.tobytes())

    def stop(self):
        with self.lock:
            # self.playing_event.clear() 
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

    def pause(self):
        self.stop()

    def set_session(self, session):
        self.session = session

    def get_player_start_time(self):
        return self.start_time
    
    def get_time_file_dict(self):
        return self.time_file_dict
    
    # def is_playing(self):
    #     # This method returns whether the playing event is set (True if playing)
    #     return self.playing_event.is_set()
    
    # def set_playing_event(self):
    #     self.playing_event.set()
            

