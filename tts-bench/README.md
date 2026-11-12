# tts-bench/

Every file in this folder with its own one-line description (a document's title, or a script's Purpose line). A blank means the file does not state one.

| File | Description |
|---|---|
| [arms-narrator-pairs.json](arms-narrator-pairs.json) |  |
| [check_intelligibility.py](check_intelligibility.py) | Gate TTS renders on whether they are actually intelligible English, by ASR-vs-known-text WER. |
| [render_longform.py](render_longform.py) | Render minutes-long narration with Chatterbox at a NAMED config, by sentence-chunking so no single generate() call approaches the model's token ceiling. |

**Folders:** [corpus/](corpus/) · [results/](results/)
