def process_file(filepath:str):
    import torch
    import torchaudio
    from datasets import load_metric, Dataset
    from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor, Wav2Vec2ProcessorWithLM
    import kenlm
    from pyctcdecode import build_ctcdecoder
    from IPython.display import Audio
    from pathlib import Path
    import json

    vad_model, vad_utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                model='silero_vad',
                                # force_reload=True
                                )

    (get_speech_timestamps,
    save_audio,
    read_audio,
    VADIterator,
    collect_chunks) = vad_utils

    wav = read_audio(filepath, sampling_rate=16000)
    vad_ts=get_speech_timestamps(wav, vad_model, sampling_rate=16000, speech_pad_ms=500, return_seconds=True)
    # print(f'Found {len(vad_ts)} segments')

    from numpy import ceil


    def resample(ts, max_gap=15, max_len=20):
        ids_to_drop = []
        for i, s in enumerate(ts):
            if s["end"] - s["start"] > max_len:
                print(
                    f"Error: max_len ({max_len}) is smaller than one of the segments ({s})!"
                )

                ids_to_drop.append(i)
        if ids_to_drop != []:
            new_ts = []
            for i in range(len(ts)):
                if i in ids_to_drop:
                    continue
                new_ts.append(ts[i])

        gts = []
        g = [ts[0]]
        for s in ts[1:]:
            if s["start"] - g[-1]["end"] < max_gap:
                g.append(s)
            else:
                gts.append(g)
                g = [s]
        gts.append(g)
        ret = []
        for g in gts:
            l = g[-1]["end"] - g[0]["start"]
            split_num = ceil(l / max_len)
            if split_num > 1:
                min_len = l / split_num
                start = g[0]["start"]
                end = g[0]["end"]
                for s in g[1:]:
                    if s["end"] - start > max_len or end - start > min_len:
                        ret.append({"start": start, "end": end})
                        start = s["start"]
                        end = s["end"]
                    else:
                        end = s["end"]
                ret.append({"start": start, "end": end})
            else:
                ret.append({"start": g[0]["start"], "end": g[-1]["end"]})
        return ret
    ts=resample(vad_ts)
    # print(f'Found {len(ts)} segments')
    # print(ts)


    from numpy import linspace, zeros, logical_and

    wav_data = wav.numpy()
    T = wav_data.size / 16000.0
    t = linspace(0, T, wav_data.size)


    sil = zeros(10 * (int(T) + 1))  # 10 pts per second
    sil_x = linspace(0, T, sil.size)

    for n, tx in enumerate(ts):
        m = logical_and(sil_x >= tx["start"], sil_x <= tx["end"])
        sil[m] = (n & 1) + 1

    model_name = "classla/wav2vec2-xls-r-parlaspeech-hr"
    device = "cuda"

    model = Wav2Vec2ForCTC.from_pretrained(model_name).to(device)
    processor = Wav2Vec2Processor.from_pretrained(model_name)

    sampling_rate = 16000

    files = {"sample": Path(filepath)}

    ds_dict = {"file": [], "start": [], "end": []}
    for seg in ts:
        ds_dict["file"].append("sample")
        ds_dict["start"].append(seg["start"])
        ds_dict["end"].append(seg["end"])
    ds = Dataset.from_dict(ds_dict)

    wavcache = {}


    def map_to_array(batch):
        if batch["file"] in wavcache:
            speech = wavcache[batch["file"]]
        else:
            path = files[batch["file"]]
            speech, _ = torchaudio.load(path)
            speech = speech.squeeze(0).numpy()
            wavcache[batch["file"]] = speech
        sstart = int(batch["start"] * sampling_rate)
        send = int(batch["end"] * sampling_rate)
        batch["speech"] = speech[sstart:send]
        return batch


    ds = ds.map(map_to_array)

    # vocab_dict = processor.tokenizer.get_vocab()
    # sorted_dict = {k.lower(): v for k, v in sorted(vocab_dict.items(), key=lambda item: item[1])}
    # decoder = build_ctcdecoder(list(sorted_dict.keys()),'danijelscode/lm.arpa',alpha=0.5,beta=1.0)
    
    def map_to_pred(batch):
        features = processor(
            batch["speech"], sampling_rate=sampling_rate, padding=True, return_tensors="pt"
        )
        input_values = features.input_values.to(device)
        attention_mask = features.attention_mask.to(device)
        with torch.no_grad():
            logits = model(input_values, attention_mask=attention_mask).logits
        pred_ids = torch.argmax(logits, dim=-1)
        batch["predicted"] = processor.batch_decode(pred_ids)
        return batch

    # def map_to_pred_lm(batch):
    #     features = processor(batch["speech"], sampling_rate=16000, padding=True, return_tensors="pt")
    #     input_values = features.input_values.to(device)
    #     attention_mask = features.attention_mask.to(device)
    #     with torch.no_grad():
    #         logits = model(input_values,attention_mask=attention_mask).logits.cpu().numpy()[0]    
    #     batch["predicted"] = decoder.decode(logits)
    #     return batch



    result = ds.map(map_to_pred, batched=True, batch_size=4)
    df = result.to_pandas().drop(columns=["speech"])
    del result

    # result_lm = ds.map(map_to_pred_lm)
    # df_lm = result_lm.to_pandas().drop(columns=["speech"])
    # del result_lm
    df["file"] = filepath
    # df["predicted_lm"] = df_lm.predicted
    import torch
    torch.cuda.empty_cache()
    return df
