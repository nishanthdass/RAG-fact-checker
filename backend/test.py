import whisperx
import torch

# Set the device (cuda if GPU is available, otherwise cpu)
device = "cpu"

# Load the WhisperX model on the specified device
model = whisperx.load_model("large-v2", device, compute_type="float32")

# Perform transcription on an audio file
result = model.transcribe("conference.wav")

# Print the result
print(result)
