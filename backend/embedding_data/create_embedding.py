from pyannote.audio import Pipeline, Model, Inference
from pyannote.core import Segment
import numpy as np




pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1",
                        use_auth_token="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")
inference_model = Model.from_pretrained("pyannote/embedding", 
                        use_auth_token="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")


diarize_bank = []

def create_embedding(file_name):
    diarization = pipeline(file_name)
    inference = Inference(inference_model, window="whole")

    speaker_embedding = None
    for turn, _, label in diarization.itertracks(yield_label=True):
        print(turn, label, _)
        segment = Segment(turn.start, turn.end)
        print(segment)
        speaker_embedding = inference.crop(file_name, segment)

        diarize_bank.append(speaker_embedding)


create_embedding("kamala diarization.wav")
np.save("kamala_embedding.npy", np.array(diarize_bank))

loaded_embedding = np.load("kamala_embedding.npy")
print(loaded_embedding)
    