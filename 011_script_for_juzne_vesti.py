import pandas as pd
from tqdm.auto import tqdm
from myutils import process_file
corpus = pd.read_csv("006_crawling_juznevesti.csv")
dfs = []
for i, path in tqdm(enumerate(corpus.path)):
    try:
        dfs.append(process_file(path))
    except Exception as e:
        raise e
        print(f"Error at file nr {i}.")
df = pd.concat(dfs, ignore_index=True)

df.to_csv("011_segments.csv", index=False)