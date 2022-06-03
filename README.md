# task13

# Addendum 2022-06-02T07:18:07

Files are here: https://web.archive.org/web/20070221010838/http://www.b92.net/info/emisije/poligraf.php?yyyy=2007&mm=02&nav_id=232420 

https://web.archive.org/web/20070225180012/http://www3.b92.net/mp3/Poligraf-2007-02-13-18-55.mp3

I first converted the audio to 16kHz wav mono file. Then I tried just jamming all of the data in the model to see if it will work. It didn't:

```
RuntimeError: [enforce fail at alloc_cpu.cpp:73] . DefaultCPUAllocator: can't allocate memory: you tried to allocate 404424771136 bytes. Error code 12 (Cannot allocate memory)
```

So we shall need some splitting. But first I can try inputting just the first 20 seconds.



# Addendum 2022-06-02T11:34:08

I found that I can input 10 minutes worth of audio and the model still works. This comes at a cost: where one minute of data takes 11s to transcribe, 10 minutes takes 11 minutes, which is a whopping 18dB slower.

I still chose that option because this means we will have less aligning to do.

# Addendum 2022-06-03T12:06:33

Finally managed to run all models. The metrics are not stellar:

| model                                           |      wer |      cer |
|:------------------------------------------------|---------:|---------:|
| classla/wav2vec2-xls-r-parlaspeech-hr-lm        | 0.661052 | 0.488822 |
| classla/wav2vec2-xls-r-parlaspeech-hr           | 0.692956 | 0.459903 |
| classla/wav2vec2-large-slavic-parlaspeech-hr    | 0.801429 | 0.573916 |
| classla/wav2vec2-large-slavic-parlaspeech-hr-lm | 0.75804  | 0.616048 |

The transcript were diffed and are ready for inspection in directory [diffs](diffs).