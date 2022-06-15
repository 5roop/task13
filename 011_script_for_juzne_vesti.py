import pandas as pd
from tqdm.auto import tqdm
from utils import process_file
corpus = pd.read_csv("006_crawling_juznevesti.csv")
dfs = []
for i in tqdm(corpus.path):
    import torch
    torch.cuda.empty_cache()
    try:
        dfs.append(process_file(i))
    except Exception as e:
        raise e
        print("Didn't work... still getting errors.")
df = pd.concat(dfs, ignore_index=True)

df.to_csv("011_segments.csv", index=False)