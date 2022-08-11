# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
from IPython import get_ipython

# %%
import torch
from numba import cuda
cuda.select_device(0)
cuda.close()
cuda.select_device(0)

torch.cuda.empty_cache()

# %% [markdown]
# ## Reading the transcripts

# %%
import pandas as pd
import numpy as np
f = "026_JV_segments_splits.jsonl"
transcript_column = "raw_transcript__matched_on_kaldi"
model_name_or_path = "facebook/wav2vec2-xls-r-300m"
repo_name = "model_01_preprocessed"
df = pd.read_json(f, orient="records", lines=True)

# def preprocess(s: str) -> str:
#     from string import punctuation
#     s = s.replace("JV:", "")
#     for pun in punctuation:
#         s = s.replace(pun, "")
#     return " ".join(
#         s.split()
#     ).casefold()

def preprocess(text: str):
    from parse import compile
    from string import punctuation

    p = compile("{hit:d}.")
    in_list = text.split()
    out_list = list()
    for seg in in_list:
        parse_result = p.parse(seg)
        if parse_result:
            # We got a number with a dot afterward:
            out_list.append(seg.lower())
        else:
            out_list.append(seg.translate(str.maketrans("", "", punctuation)).lower())
    return " ".join(out_list)

df["path"] = df.segment_file.apply(lambda s: dict(path=s, bytes=None))
df["sentence"] = df[transcript_column].apply(preprocess)
test_on = "dev"

df = df[["path", "sentence", "split"]]
df.head()

# %% [markdown]
# ## performing the train_test split

# %%
common_voice_train_df = df.loc[df.split=="train", :].copy()
common_voice_test_df = df.loc[df.split==test_on, :].copy()


common_voice_train_df.reset_index(drop=True, inplace=True)
common_voice_test_df.reset_index(drop=True, inplace=True)

# %% [markdown]
# ## Reading the audio file with `datasets.Audio`

# %%
import datasets
from datasets import load_dataset, load_metric, Audio
def load_audio(path):
    return datasets.Audio(sampling_rate=16000).decode_example(path)

# Adding audio
common_voice_train_df.loc[:, "audio"] = common_voice_train_df.path.apply(load_audio)
common_voice_test_df.loc[:, "audio"] = common_voice_test_df.path.apply(load_audio)

# Initiating a dataset from pandas dataframe
common_voice_train_dataset = datasets.Dataset.from_pandas(common_voice_train_df)
common_voice_test_dataset = datasets.Dataset.from_pandas(common_voice_test_df)

# %% [markdown]
# ## Preparing the training pipeline

# %%
# from transformers import Wav2Vec2CTCTokenizer
# from transformers import Wav2Vec2FeatureExtractor
# from transformers import Wav2Vec2Processor
# tokenizer = Wav2Vec2CTCTokenizer.from_pretrained(
#     "./", unk_token="[UNK]", pad_token="[PAD]", word_delimiter_token="|")

# feature_extractor = Wav2Vec2FeatureExtractor(
#     feature_size=1, sampling_rate=16000, padding_value=0.0, do_normalize=True, return_attention_mask=True)

# processor = Wav2Vec2Processor(
#     feature_extractor=feature_extractor, tokenizer=tokenizer)

try:
    from transformers import Wav2VecProcessor
    processor = Wav2Vec2Processor.from_pretrained(model_name_or_path,)
except:
    from transformers import Wav2Vec2CTCTokenizer, Wav2Vec2FeatureExtractor, Wav2Vec2Processor
    tokenizer = Wav2Vec2CTCTokenizer.from_pretrained(
        "./", unk_token="[UNK]", pad_token="[PAD]", word_delimiter_token=" "
    )
    feature_extractor = Wav2Vec2FeatureExtractor(
        feature_size=1,
        sampling_rate=16000,
        padding_value=0.0,
        do_normalize=True,
        return_attention_mask=True,
    )
    processor = Wav2Vec2Processor(feature_extractor=feature_extractor, tokenizer=tokenizer)

import torch

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

@dataclass
class DataCollatorCTCWithPadding:
    """
    Data collator that will dynamically pad the inputs received.
    Args:
        processor (:class:`~transformers.Wav2Vec2Processor`)
            The processor used for proccessing the data.
        padding (:obj:`bool`, :obj:`str` or :class:`~transformers.tokenization_utils_base.PaddingStrategy`, `optional`, defaults to :obj:`True`):
            Select a strategy to pad the returned sequences (according to the model's padding side and padding index)
            among:
            * :obj:`True` or :obj:`'longest'`: Pad to the longest sequence in the batch (or no padding if only a single
              sequence if provided).
            * :obj:`'max_length'`: Pad to a maximum length specified with the argument :obj:`max_length` or to the
              maximum acceptable input length for the model if that argument is not provided.
            * :obj:`False` or :obj:`'do_not_pad'` (default): No padding (i.e., can output a batch with sequences of
              different lengths).
    """

    processor: Wav2Vec2Processor
    padding: Union[bool, str] = True
    padding: Union[bool, str] = True
    # padding = True

    def __call__(self, features: List[Dict[str, Union[List[int], torch.Tensor]]]) -> Dict[str, torch.Tensor]:
        # split inputs and labels since they have to be of different lenghts and need
        # different padding methods
        input_features = [{"input_values": feature["input_values"]} for feature in features]
        label_features = [{"input_ids": feature["labels"]} for feature in features]

        batch = self.processor.pad(
            input_features,
            padding=self.padding,
            return_tensors="pt",
        )
        with self.processor.as_target_processor():
            labels_batch = self.processor.pad(
                label_features,
                padding=self.padding,
                return_tensors="pt",
            )

        # replace padding with -100 to ignore loss correctly
        labels = labels_batch["input_ids"].masked_fill(labels_batch.attention_mask.ne(1), -100)

        batch["labels"] = labels

        return batch

data_collator = DataCollatorCTCWithPadding(processor=processor, padding=True)



from transformers import Trainer
from transformers import TrainingArguments
from transformers import Wav2Vec2ForCTC
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
import torch


def prepare_dataset(batch):
    audio = batch["audio"]

    # batched output is "un-batched"
    batch["input_values"] = processor(
        audio["array"], sampling_rate=audio["sampling_rate"]).input_values[0]
    batch["input_length"] = len(batch["input_values"])

    with processor.as_target_processor():
        batch["labels"] = processor(batch["sentence"]).input_ids
    return batch


common_voice_train_mapped = common_voice_train_dataset.map(
    prepare_dataset, remove_columns=common_voice_train_dataset.column_names)
common_voice_test_mapped = common_voice_test_dataset.map(
    prepare_dataset, remove_columns=common_voice_test_dataset.column_names)


# %%
wer_metric = load_metric("wer")
cer_metric = load_metric("cer")
def compute_metrics(pred):
    pred_logits = pred.predictions
    pred_ids = np.argmax(pred_logits, axis=-1)

    pred.label_ids[pred.label_ids == -100] = processor.tokenizer.pad_token_id

    pred_str = processor.batch_decode(pred_ids)
    # we do not want to group tokens when computing the metrics
    label_str = processor.batch_decode(pred.label_ids, group_tokens=False)

    wer = wer_metric.compute(predictions=pred_str, references=label_str)
    cer = cer_metric.compute(predictions=pred_str, references=label_str)
    return {"wer": wer, "cer": cer}

max_input_length_in_sec = 20
common_voice_train_mapped = common_voice_train_mapped.filter(lambda x: x < max_input_length_in_sec * processor.feature_extractor.sampling_rate, input_columns=["input_length"])

model = Wav2Vec2ForCTC.from_pretrained(
    model_name_or_path,
    attention_dropout=0.0,
    hidden_dropout=0.0,
    feat_proj_dropout=0.0,
    mask_time_prob=0.05,
    layerdrop=0.0,
    ctc_loss_reduction="mean",
    pad_token_id=processor.tokenizer.pad_token_id,
    vocab_size=len(processor.tokenizer),
)

# model.freeze_feature_extractor()

from transformers import TrainingArguments

training_args = TrainingArguments(
  output_dir=repo_name,
  group_by_length=True,
  per_device_train_batch_size=16,
  gradient_accumulation_steps=4,
  evaluation_strategy="epoch",
  save_strategy="epoch",
  num_train_epochs=20,
  gradient_checkpointing=True,
  fp16=True,
  #save_steps=400,
  #eval_steps=400,
  logging_steps=400,
  learning_rate=3e-4,
  warmup_steps=500,
  save_total_limit=9,
  push_to_hub=False,
)

from transformers import Trainer

trainer = Trainer(
    model=model,
    data_collator=data_collator,
    args=training_args,
    compute_metrics=compute_metrics,
    train_dataset=common_voice_train_mapped,
    eval_dataset=common_voice_test_mapped,
    tokenizer=processor.feature_extractor,
)

trainer.train()


