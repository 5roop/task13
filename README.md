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



# Addendum 2022-06-06T07:45:14

I completed the transcription of [this video](https://pescanik.net/ruske-ideje-i-srpske-replike/) as per the Skype chat  with Nikola on Friday, 12:55 PM.

| model                                           |      wer |      cer |
|:------------------------------------------------|---------:|---------:|
| classla/wav2vec2-xls-r-parlaspeech-hr-lm        | 0.582383 | 0.41452  |
| classla/wav2vec2-xls-r-parlaspeech-hr           | 0.60829  | 0.402753 |
| classla/wav2vec2-large-slavic-parlaspeech-hr-lm | 0.633161 | 0.480184 |
| classla/wav2vec2-large-slavic-parlaspeech-hr    | 0.660449 | 0.461923 |

The metrics are a bit lower, but the same ranking is seen (xls-r > large-slavic, LM helps wer but increases cer.)

# Addendum 2022-06-06T09:43:03

## Analysis of possible future data sources:

### pescanik.net

Sample size: 2

Transcripts are heavily edited. A lot of manual preprocessing would have to be done to correct them (at least as much time as the length of the audios we acquire).

We would have to download the resources manually. 

Audio: hosted on vimeo and soundcloud (difficult to scrape)

There is quite a lot of resources available though.

### Južne vesti

Sample size: 3


Transcripts slightly edited (deleted 'ot prilike', 'znate kako eerrrm', 'eto', 'i,i,i, kako bih rekao...', 'i tako dalje i tako dalje'), some bad spelling (Nišu -> Nipu, mo smo -> mi smo, diektor -> direktor), multiple speakers speaking at once in some cases .

Video hosted on yt (easier to scrape)


### B92.net

Accessed via web archive. Difficult to navigate, on the sites with transcripts there is no indication where the audio recording is. -> the searching would be difficult, but the scrapping would be the easiest yet.

Sample size: 1

Transcripts the nicest. Sometimes the speaker is interrupted and then the transcript gets cut.

Current site (not accessed through web archive) seems not to have the same file structure, nor the transcripts for the content.

# Addendum 2022-06-06T12:56:54

Next step was a sample from Južne Vesti [specifically this one](https://www.juznevesti.com/15-minuta/Marko-Nedeljkovic.sr.html):

| model                                           |      wer |      cer |
|:------------------------------------------------|---------:|---------:|
| classla/wav2vec2-xls-r-parlaspeech-hr-lm        | 0.67979  | 0.544579 |
| classla/wav2vec2-xls-r-parlaspeech-hr           | 0.701662 | 0.53524  |
| classla/wav2vec2-large-slavic-parlaspeech-hr    | 0.748031 | 0.557548 |
| classla/wav2vec2-large-slavic-parlaspeech-hr-lm | 0.715223 | 0.565849 |

# Designing the scrapper for Južne Vesti:

We need text and yt-audio. For now I assume the URL will be given as an input, if needed, we can design a crawler to get them later.

For now I will use the same [link](https://www.juznevesti.com/15-minuta/Marko-Nedeljkovic.sr.html) as above.



# Addendum 2022-06-07T09:42:58

I won't be able to download the videos here. I plan to do that on my PC where I have plenty of space and time available.