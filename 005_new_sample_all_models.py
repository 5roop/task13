# %%
import os

import numpy as np
import soundfile as sf
import torch
from transformers import Wav2Vec2ForCTC, Wav2Vec2ProcessorWithLM, Wav2Vec2Processor



models = [
    "classla/wav2vec2-xls-r-parlaspeech-hr-lm",
    "classla/wav2vec2-xls-r-parlaspeech-hr",
    "classla/wav2vec2-large-slavic-parlaspeech-hr",
    "classla/wav2vec2-large-slavic-parlaspeech-hr-lm",
]
results = list()
for model_name in models:
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    # load model and tokenizer
    if model_name.endswith("-lm"):
        processor = Wav2Vec2ProcessorWithLM.from_pretrained(model_name,)
    else:
        processor = Wav2Vec2Processor.from_pretrained(model_name, pad_token="[PAD]")
    model = Wav2Vec2ForCTC.from_pretrained(model_name)
    # read the wav file
    speech, sample_rate = sf.read("audio_3.wav")

    overlap_seconds = 1

    indices = np.arange(
        0, speech.shape[0], 10 * 60 * sample_rate, dtype=int
    ).tolist() + [-1]

    transcripts = list()
    for start, stop in zip(indices[0:-2], indices[1:]):
        # If overlap would make the segment go
        # over the end, correct stop variable:
        if stop + overlap_seconds * sample_rate >= speech.shape[0]:
            stop = -1
        speech_segment = speech[start:stop]
        inputs = processor(
            speech_segment, sampling_rate=sample_rate, return_tensors="pt"
        )
        with torch.no_grad():
            logits = model(**inputs).logits
        try:
            transcription = processor.batch_decode(logits.numpy()).text[0]
        except:
            prediction_ids = torch.argmax(logits, dim=-1)
            transcription = processor.batch_decode(prediction_ids)[0]

        transcripts.append(transcription)
    results.append({"model": model_name, "transcription": " ".join(transcripts)})

import pandas as pd

pd.DataFrame(data=results).to_csv("005_all_models_transcriptions.csv", index=False)



