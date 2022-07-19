# %%
import pandas as pd
import numpy as np

mer = pd.read_json("021_JV_segments_with_metadata.jsonl", orient="records", lines=True)
mer = mer[~mer.file.str.contains("_BzZf0fGg0E")]
corp = pd.read_json("020_JV_with_metadata.jsonl", orient="records", lines=True)

def corpus_handler(s:str) -> str:
    """For corpus transcripts."""
    from string import punctuation
    for p in punctuation:
        s = s.replace(p, "")
    return " ".join(
        s.replace("JV:", "").split()
    ).casefold()

def segment_handler(s:str) -> str:
    return s.replace("<anchor_start>", "").replace("<anchor_end>", "")

def find_optimal_subset(segment, full, step=1, limit = None):
    from fuzzywuzzy.fuzz import ratio
    from tqdm.auto import tqdm
    segment = segment.split()
    full = full.split()
    best = 0
    best_start, best_end = 0, -1
    tqdm = lambda x: x
    for start in tqdm(range(0, len(full) if not limit else 2*limit, step)):
        for end in range(len(full)- 2*limit if limit else start, len(full), step):
            try:
                subset = full[start:end]
                current = ratio(
                    segment_handler(" ".join(segment)),
                    corpus_handler(" ".join(subset))
                        )
                # print(start, end, current, subset)
                if current >= best:
                    best_start, best_end = start, end
                    best = current
            except IndexError:
                continue
    if step != 1:
        best_start = max((best_start - step, 0))
        best_end   = min((best_end   + step, len(full)))
    return " ".join(
        full[best_start:best_end]
    )

def match_kaldi(row):
    segments_file = row["file"]
    full_transcript = corp[corp.path == segments_file].transcript.values[0]
    segments_transcript = row["kaldi_transcript"]

    coarse = find_optimal_subset(segments_transcript, full_transcript, step=100)
    medium = find_optimal_subset(segments_transcript,  coarse, step=10, limit=100)
    fine = find_optimal_subset(segments_transcript,  medium, step=1, limit=10)
    return fine

from concurrent.futures import ProcessPoolExecutor

with ProcessPoolExecutor(max_workers=30) as executor:
    results = executor.map(match_kaldi, [row for i, row in mer.iterrows()])
mer["Raw_transcript__matched_on_kaldi"] = results

# %%
mer.to_json("025_segments_matched_with_raw.jsonl", orient="records", lines=True)

# %%
def match_asr(row):
    segments_file = row["file"]
    full_transcript = corp[corp.path == segments_file].transcript.values[0]
    segments_transcript = row["asr_transcription"]

    coarse = find_optimal_subset(segments_transcript, full_transcript, step=100)
    medium = find_optimal_subset(segments_transcript,  coarse, step=10, limit=100)
    fine = find_optimal_subset(segments_transcript,  medium, step=1, limit=10)
    return fine


from concurrent.futures import ProcessPoolExecutor

with ProcessPoolExecutor(max_workers=30) as executor:
    results = executor.map(match_kaldi, [row for i, row in mer.iterrows()])
mer["Raw_transcript__matched_on_asr"] = results

# %%
mer.to_json("025_segments_matched_with_raw.jsonl", orient="records", lines=True)


