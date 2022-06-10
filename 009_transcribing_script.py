# %%
from itertools import groupby
import torch
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
from transformers import Wav2Vec2FeatureExtractor
from transformers import Wav2Vec2Processor, Wav2Vec2CTCTokenizer
import soundfile as sf

def get_words_and_times(
    speech,
    model_name = "classla/wav2vec2-xls-r-parlaspeech-hr"
):
    tokenizer = Wav2Vec2CTCTokenizer.from_pretrained(
    model_name, unk_token="[UNK]", 
    #pad_token="[PAD]", 
    #word_delimiter_token="|"
    )
    feature_extractor = Wav2Vec2FeatureExtractor(
        feature_size=1, sampling_rate=16000, padding_value=0.0, do_normalize=True, return_attention_mask=True)
    processor = Wav2Vec2Processor(
        feature_extractor=feature_extractor, tokenizer=tokenizer)
    model = Wav2Vec2ForCTC.from_pretrained(model_name).cuda()
    # audio_filepath = df.path[0]
    # speech, sample_rate = sf.read(audio_filepath)
    input_values = processor(speech, sampling_rate=sample_rate, return_tensors="pt").input_values.cuda()

    logits = model(input_values).logits

    predicted_ids = torch.argmax(logits, dim=-1)
    transcription = processor.decode(predicted_ids[0]).lower()

    ##############
    # this is where the logic starts to get the start and end timestamp for each word
    ##############
    words = [w for w in transcription.split() if len(w) > 0]
    predicted_ids = predicted_ids[0].tolist()
    duration_sec = input_values.shape[1] / sample_rate


    ids_w_time = [(i / len(predicted_ids) * duration_sec, _id) for i, _id in enumerate(predicted_ids) if _id != processor.tokenizer.pad_token_id]
    times_and_tokens = [(i, processor.tokenizer.convert_ids_to_tokens(j) )for i, j in ids_w_time]
    indices_to_pop = list()
    for i, tt in enumerate(times_and_tokens):
        try:
            if tt[1] == times_and_tokens[i+1][1]:
                indices_to_pop.append(i)
        except IndexError:
            continue
    for i in sorted(indices_to_pop)[::-1]:
        times_and_tokens.pop(i)
    word_starts = []
    word_ends = []
    word_started = True
    for i, (time, token) in enumerate(times_and_tokens):
        if word_started:
            word_starts.append(time)
            word_started = False
        if token == " ":
            word_ends.append(time)
            word_started = True
        if i == len(times_and_tokens) -1:
            word_ends.append(time)
    return words, word_starts, word_ends

def process_file(filename, model_name="classla/wav2vec2-xls-r-parlaspeech-hr"):
    import numpy as np
    speech, sample_rate = sf.read(filename)
    overlap_seconds = 1
    indices = np.arange(
        0, speech.shape[0], 10 * 60 * sample_rate, dtype=int
    ).tolist() + [-1]

    transcript = ""
    word_starts = list()
    word_ends = list()
    for start, stop in zip(indices[0:-2], indices[1:]):
        # If overlap would make the segment go
        # over the end, correct stop variable:
        if stop + overlap_seconds * sample_rate >= speech.shape[0]:
            stop = -1
        speech_segment = speech[start:stop]
        words, starts, stops = get_words_and_times(speech_segment, model_name)
        transcript = transcript + " " + " ".join(words)
        word_starts.extend([i + start for i in starts])
        word_ends.extend([i + start for i in stops])
    return transcript, word_starts, word_ends



# %%
import pandas as pd

df = pd.read_csv("006_crawling_juznevesti.csv")

df.path[0]

# %%
process_file(_)

# %%

df["transcript"] = ""
df["word_starts"] = []
df["word_ends"] = []
for i in range(df.shape[0]):
    path = df.path[i]
    words, starts, ends = process_file(path)
    df.loc["transcript", i] = words
    df.loc["word_starts", i] = starts
    df.loc["word_ends", i] = ends
    df.to_csv("009_transcripted.csv", index=False)


