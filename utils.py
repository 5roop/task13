


def get_words_and_times(
    speech, sample_rate, model_name="classla/wav2vec2-xls-r-parlaspeech-hr"
):
    from itertools import groupby

    import soundfile as sf
    import torch
    from transformers import (Wav2Vec2CTCTokenizer, Wav2Vec2FeatureExtractor,
                              Wav2Vec2ForCTC, Wav2Vec2Processor)
    tokenizer = Wav2Vec2CTCTokenizer.from_pretrained(
        model_name,
        unk_token="[UNK]",
        # pad_token="[PAD]",
        # word_delimiter_token=" "
    )
    feature_extractor = Wav2Vec2FeatureExtractor(
        feature_size=1,
        sampling_rate=sample_rate,
        padding_value=0.0,
        do_normalize=True,
        return_attention_mask=True,
    )
    processor = Wav2Vec2Processor(
        feature_extractor=feature_extractor, tokenizer=tokenizer
    )
    model = Wav2Vec2ForCTC.from_pretrained(model_name).cuda()
    input_values = processor(
        speech, sampling_rate=sample_rate, return_tensors="pt"
    ).input_values.cuda()

    logits = model(input_values).logits

    predicted_ids = torch.argmax(logits, dim=-1)
    transcription = processor.decode(predicted_ids[0]).lower()

    ##############
    # this is where the logic starts to get the start and end timestamp for each word
    ##############
    words = [w for w in transcription.split() if len(w) > 0]
    predicted_ids = predicted_ids[0].tolist()
    duration_sec = input_values.shape[1] / sample_rate

    ids_w_time = [
        (i / len(predicted_ids) * duration_sec, _id)
        for i, _id in enumerate(predicted_ids)
        if _id != processor.tokenizer.pad_token_id
    ]
    times_and_tokens = [
        (i, processor.tokenizer.convert_ids_to_tokens(j)) for i, j in ids_w_time
    ]
    indices_to_pop = list()
    for i, tt in enumerate(times_and_tokens):
        try:
            if tt[1] == times_and_tokens[i + 1][1]:
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
        if i == len(times_and_tokens) - 1:
            word_ends.append(time)
    return words, word_starts, word_ends


def process_file(
    filename, model_name="classla/wav2vec2-xls-r-parlaspeech-hr", lim_minutes=0.25
):
    from itertools import groupby

    import numpy as np
    import soundfile as sf
    import torch
    from transformers import (Wav2Vec2CTCTokenizer, Wav2Vec2FeatureExtractor,
                              Wav2Vec2ForCTC, Wav2Vec2Processor)

    speech, sample_rate = sf.read(filename)
    indices = np.arange(
        0, speech.shape[0], int(lim_minutes * 60 * sample_rate), dtype=int
    )
    transcription = ""
    word_starts = []
    word_ends = []
    overlap_seconds = 1
    for start, stop in zip(indices, indices[1:]):
        speech_segment = speech[start : stop + int(sample_rate * overlap_seconds)]
        words, starts, ends = get_words_and_times(
            speech_segment, sample_rate, model_name=model_name
        )
        transcription += " " + " ".join(words)
        word_starts += [i + start / sample_rate for i in starts]
        word_ends += [i + start / sample_rate for i in ends]
    start, stop = indices[-1], speech.shape[0]
    speech_segment = speech[start:]
    words, starts, ends = get_words_and_times(
        speech_segment, sample_rate, model_name=model_name
    )
    transcription += " " + " ".join(words)
    word_starts += [i + start / sample_rate for i in starts]
    word_ends += [i + start / sample_rate for i in ends]

    transcription = transcription.replace("[pad]", "")
    return transcription, word_starts, word_ends
