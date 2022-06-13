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

# Addendum 2022-06-08T08:01:07

The videos are now all done, except for one, which is private. I tried watching it on the website, but even there it is private. That instance has been deleted.

All in all, is quite OK. We only failed in 1/300 cases.

The scraping in the first round yielded about 15 missing videos, but when I retried it this morning, it worked OK with the same code. Perhaps YT issued some temporary block for my IP?



# Addendum 2022-06-09T12:44:55

Nikola found a recent SABOR yt video to test on. I transcribed it on all models (this is the [file](audio/s1iBR07bVrg_clipped.wav)). I do not have the transcript for it, the model transcriptions are [here](010_some_models_transcriptions.csv), and if I take the original xls-r-parlaspeech-hr model as a base, I can compile this table of similarities:

| model                                           |      wer |       cer |
|:------------------------------------------------|---------:|----------:|
| classla/wav2vec2-xls-r-parlaspeech-hr-lm        | 0.144981 | 0.0387541 |
| classla/wav2vec2-xls-r-parlaspeech-hr           | 0        | 0         |
| classla/wav2vec2-large-slavic-parlaspeech-hr    | 0.329926 | 0.117841  |
| classla/wav2vec2-large-slavic-parlaspeech-hr-lm | 0.282528 | 0.119994  |

# Addendum 2022-06-10T08:01:50
When trying to extract temporal data with parlaspeech model, I kept hitting the CPU memory limits. I finally had to resort to 15s of data, although when running it as a pure transcriber, I can fit up to 

# Addendum 2022-06-10T14:19:24

The temporal data is quite good on small samples. On larger there is some jitter.

# Addendum 2022-06-13T07:33:51

I checked the performance once again on [this file](audio/s1iBR07bVrg_clipped.wav): at 1,2,3, and 4 minutes the transcriptions and audio match exactly. At 10 and 9 minutes the transcriptions are _leading_ for 3 seconds. At 8 minutes, the mismatch is only 1 second.

I think the way forward is to add another loop and segment files into shorter segments. Then these segments can be processed with existing machinery exactly.

# Addendum 2022-06-13T08:02:58

I noticed an interesting phenomenon. Check this transcription out:

```
vlasnika            415.23-415.33 -> OK
tvrtke              415.37-415.55 -> OK 
i                   415.57-416.41
imali               416.43-417.44
smo                 417.46-418.00
problem             418.04-418.52
imali               418.54-419.84 -> OK
smo                 419.86-420.02 -> OK
problem             420.04-420.36 -> OK
koji                420.40-420.58 -> OK
je                  420.60-420.98 -> OK
```

The middle section doesn't correspond to reality and is likely an artifact of overlapping to assure no words get missed. But if we try it without overlapping, we get this:

```
vlasnika            415.23-415.33 -> OK
tvrtke              415.37-415.55 -> OK
i                   415.57-416.42 ... too early.
imali               416.44-417.44
smo                 417.46-418.00
problem             418.04-418.52
koji                418.54-419.84
je                  419.86-419.98
```

# Addendum 2022-06-13T10:05:51

From [github](https://github.com/danijel3/CroatianSpeech) I downoaded Danijel's notebooks.  [Croatian](danijelscode/Croatian.ipynb) works like a charm. [KaldiAlign](danijelscode/KaldiAlign.ipynb) however doesn't run from the first cell onward. Issues: 

#### Running first cell already complains:

```
...
ln: failed to create symbolic link '/usr/local/bin/liblbfgs.la': Permission denied
ln: failed to create symbolic link '/usr/local/bin/missing': Permission denied
ln: failed to create symbolic link '/usr/local/bin/install-sh': Permission denied
/sbin/ldconfig.real: Can't create temporary cache file /etc/ld.so.cache~: Permission denied
```

#### Can't install openfst-python
```
ERROR: Failed building wheel for openfst-python
```