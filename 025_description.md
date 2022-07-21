# Južne vesti dataset

## Crawling and processing

The dataset was scrapped from [Južne vesti](www.juznevesti.com), programme `15 minuta`. The website has a transcript and an embedded YouTube video for every episode.

The sound from the video has been converted to 16000 Hz mono audio and saved in `audio` directory, the mp3 versions are saved in `audio_mp3`. The transcripts were saved [here](006_crawling_juznevesti.csv).

Following Danijel's tutorial the VAD-based splitting was performed. The split audio files are in `seg_audio` directory. The ASR was performed, but the raw transcript was not aligned nicely with the segments.

Everything was moved to another server and processed with Kaldi. The matches were better this time. Other than the matches word start and stop timestamps were also extracted. Before processing separators were added (double pi token for start of host speaking and tripple pi for the end.) This allowed us to separate host and guests speaking.

Lastly, the raw transcriptions were aligned with Kaldi output and ASR recordings. This was done using fuzzy string matching.


## Current dataset composition:

File `025_segments_matched_with_raw.jsonl`:
* `file`: from which whole-video-file the instance originates. The file is named after video's YT hash, e.g.: audio/58xZSVbpgkk.wav
* `segment_file`: audio file, covering only the specific instance. 
* `start`: start timestamp in seconds (of the whole-video-file)
* `end`: end timestamp in seconds (of the whole-video-file),
* `asr_transcription`: ASR transcription obtained in the process, 
* `kaldi_transcript`: Kaldi match,
* `raw_transcript__matched_on_kaldi`: raw transcriptions from the webpage (including numerals and punctuation), matched against Kaldi output, 
* `raw_transcript__matched_on_asr`: same, matched against ASR output
* `guest_name`: metadata, 
* `guest_description`: metadata, 
* `host`: metadata, 
* `kaldi_words`: a list of Kaldi words,
* `kaldi_word_starts` a list of timestamps in seconds since the beginning of the original video, describing the start of each word in column 'kaldi_words' 
* `kaldi_word_ends`: same for word ending 
* `speaker_breakdown`: a list of tuples ('host', 0, 10), describing whether the host or the guest is speaking and the start and stop timestamps of the segment
* `average_distance`: average of word-level Levenshtein distances between ASR and Kaldi, this is only valid for minor differences (it is calculated pair-wise word for word, so when one transcript is `short but wrong in some way` and the other is only `short`, the result is a perfect score)
* 'similarity_ratio': similarity ratio  between ASR and Kaldi, implementation from `fuzzywuzz.fuzz`. 

## Possible improvements:

* Can we use a better separator to cleanly delimit the host questions and not impede Kaldi?
* Since the texts to be matched are shorter than parliamentary data, perhaps something can be optimized to produce better matches? 