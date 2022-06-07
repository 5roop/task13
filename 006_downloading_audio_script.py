# %%
import pandas as pd
df = pd.read_csv("006_crawling_juznevesti.csv")
df

# %%
from tqdm.auto import tqdm
import os
import tempfile
from pathlib import Path

audiodir = Path("audio")
def download_sound(yt_hash):
    with tempfile.NamedTemporaryFile() as f:
        cmd = f"youtube-dl {yt_hash} -x --audio-format wav -o {f.name}.wav"
        os.system(cmd)

        cmd = f"ffmpeg -i {f.name}.wav -ac 1 -ar 16000 audio/{yt_hash}.wav"
        os.system(cmd)

from concurrent.futures import ProcessPoolExecutor
with ProcessPoolExecutor(max_workers=4) as executor:
    executor.map(download_sound, df.yt_hash.values)
