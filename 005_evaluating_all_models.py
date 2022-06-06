# %%
from pathlib import Path
import pandas as pd
import string
raw = Path("transcript_raw_3.txt").read_text()

# %% [markdown]
# preprocess raw: delete newlines and reporters' names, delete excess whitespace and all punctuation:

# %%
raw = raw.replace("\nVekarić:", " ").replace("\nB92:", " ").replace("\n", " ").lower()
for l in string.punctuation:
    raw = raw.replace(l, "")
raw = " ".join(raw.split())

# %%
df = pd.read_csv("005_all_models_transcriptions.csv")
df.head()

# %%
def generate_differ_content(pred:str) -> str:
    """Generate comparatively pretty diff from input predictions
    against global raw.

    Args:
        pred (str): Predictions to be compared

    Returns:
        str: Newline delimited diff.
    """
    from difflib import Differ
    differ_content = ""
    for diff in list(Differ().compare(raw.split(), pred.split()))[:500]:
        differ_content += diff + "\n"
    return differ_content

# %%
wers = []
cers = []
for i, row in df.iterrows():
    modelname = row["model"]
    pred = row["transcription"].replace("<pad>", "")
    from datasets import load_metric

    wer = load_metric("wer")
    cer = load_metric("cer")

    c = cer.compute(predictions = [pred], references = [raw])
    w = wer.compute(predictions = [pred], references = [raw])
    cers.append(c)
    wers.append(w)
    content = generate_differ_content(pred=pred)
    fname = f"""005_{modelname.replace("/", "--")}.txt"""
    p = Path("./diffs") / fname
    header = f"""Model: {modelname},\ncer: {c}, \nwer: {w}\n\n\n"""
    p.write_text(header + content)


# %%
df["cer"] = cers
df["wer"] = wers
print(df["model wer cer".split()].to_markdown(index=False))

# %%



