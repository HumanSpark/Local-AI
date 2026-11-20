<!--
# File: voices.md
# Purpose: Public voice-sample page for the Local AI data package - the production TTS voice and the candidates that lost.
# Project: sparkbench | Date: 2026-11-20
#
# Overview: Shipped as VOICES.md at the package root, with the MP3s in reports/voices/ shipped as voices/. Samples are
# re-encodes (mono 64 kbit/s MP3) of the W3 narrator-reel takes named in docs/w3-audio-rename-log.csv, plus one fresh
# Kokoro bf_emma render of the same line. Female voices only; F5-TTS and Fish (licence) and own-voice clips
# are deliberately excluded.
-->

# Voices: what the machine sounds like

## In plain English

The machine reads text aloud in one voice: a British woman's voice, cloned by the open-source Chatterbox engine from a public research recording. We picked it by ear in July 2026 after auditioning eight British female speakers and every cloning engine that would run here. Below are the samples behind that choice. Most read the same sentence, so you can compare the engines like for like. The voices and engines that lost are here too, including one that produced garbled speech.

Every sample was made on this machine. Nothing was sent to a cloud service. Files open or download when clicked; GitHub does not play audio inline.

## The line every clone reads

> "The businesses that win with AI won't be the ones with the biggest budgets. They'll be the ones who understood the problem before buying the tool."

A cloning engine needs a short recording of a real voice to copy. Ours are speakers p239 and p233 from the VCTK corpus, a public research dataset. The human recordings read a different sentence from the clones because they are corpus recordings, not renders of our line. They are included so you can hear how faithful each clone is to its source.

## Production

| sample | what it is | length |
|---|---|---|
| [01 - human reference, p239](voices/01-vctk-p239-human-reference.mp3) | The source recording: VCTK speaker p239, South West England, utterance 008 | 7 s |
| [02 - Chatterbox clone of p239](voices/02-chatterbox-p239-production.mp3) | **The production voice** reading the line | 6 s |
| [03 - Chatterbox clone of p239, long form](voices/03-chatterbox-p239-production-68s.mp3) | 227 words of sustained narration, the sample that closed the search. It took 169 s to render 68 s of audio | 68 s |

Production serves the same reference recording at the same settings these samples used (exaggeration 0.5, cfg weight 0.5, temperature 0.8). Decided by ear on 26 July 2026 ([F56](FINDINGS.md#f56)); the default voice since 1 August 2026.

## The candidates that lost

| sample | what it is | verdict |
|---|---|---|
| [04 - human reference, p233](voices/04-vctk-p233-human-reference.mp3) | VCTK speaker p233, Staffordshire, utterance 008 | Second choice of the two voices |
| [05 - Chatterbox clone of p233](voices/05-chatterbox-p233-runner-up.mp3) | Same engine, the other voice | Accepted, lost the tie-break to p239 |
| [06 - VoxCPM2 clone of p239](voices/06-voxcpm2-p239-lost.mp3) | Same voice as production, a different engine | Lost to Chatterbox |
| [07 - VoxCPM2 clone of p233](voices/07-voxcpm2-p233-lost.mp3) | The runner-up voice, a different engine | Lost to Chatterbox |
| [08 - Kokoro, voice bf_emma](voices/08-kokoro-bf-emma-fallback.mp3) | A built-in voice, no cloning. Rendered on 20 November 2026 through the live fallback route | Rejected by ear in July. Kept as an opt-in fallback |
| [09 - CosyVoice3 clone of p239](voices/09-cosyvoice3-p239-garbled.mp3) | A third cloning engine | **Garbled.** It fails its own documented example on this graphics chip ([F55](FINDINGS.md#f55)) |

Every clone from 02 to 07 passed an automatic intelligibility check: a speech-to-text model transcribed it with no word errors against the requested line. Sample 09 is why that check exists. Three CosyVoice3 renders like it passed every duration and level check, and were played to a human listener before anyone noticed they were not English.

## Numbers, dates and symbols have to be written out first

Chatterbox has no number handling of its own. We checked the installed package: its text clean-up rewrites punctuation only, and nothing in it spells out digits, ordinals or dates. A numeral reaches the model raw, and what comes out is whatever the model learned. So every script is rewritten into words before it is spoken. The two samples below are the same sentence in the production voice, rendered on 20 November 2026.

| sample | text given to the engine |
|---|---|
| [10 - as written](voices/10-numbers-raw.mp3) | On 2026-07-19 we cut costs by 23.5% to £4.2m, the 3rd cut since 2005. The server has 128GB, and the report is on humanspark.ai. |
| [11 - written out first](voices/11-numbers-speakable.mp3) | On the nineteenth of July, twenty twenty-six we cut costs by twenty-three point five percent to four point two million pounds, the third cut since two thousand and five. The server has one hundred and twenty-eight gigabytes, and the report is on humanspark dot A I. |

When Whisper transcribed sample 10, the pound sign was gone ("to 4.2m") and "128GB" came back as "108 GBs". Sample 11 came back correct.

That transcript also shows why our automatic intelligibility check cannot catch this class of error. Whisper turns spoken numbers back into numerals, so "two hundred and thirty percent" and "two three zero percent" both transcribe as "230%" and score the same. Unit tests on the rewriting step are the only real check.

The rules, each added after a real script got it wrong:

| written | spoken | why it needs a rule |
|---|---|---|
| 2026-07-19 | the nineteenth of July, twenty twenty-six | Dates are read as ordinals in British day-month order |
| 2024 / 2005 / 1900 | twenty twenty-four / two thousand and five / nineteen hundred | Years are not said as plain numbers, and 2001 to 2009 break the usual pattern |
| 21st | twenty-first | Only the last word changes, and first, second, third, fifth, eighth, ninth and twelfth are irregular |
| £4.2m, $4B | four point two million pounds, four billion dollars | The size word goes before the currency word, not after it |
| 23.5%, 10-20% | twenty-three point five percent, ten to twenty percent | Decimals are read digit by digit after "point", and ranges are read as ranges |
| 128GB, 8am, 3x | one hundred and twenty-eight gigabytes, eight a.m., three times | Units glued to a number. An unknown unit is left alone and reported, not guessed |
| humanspark.ai | humanspark dot A I | Two-letter domain endings are spelled out, while "com" and "org" are said as words |
| GPT-4, GPT-5.2 | left as written | Product names are not numbers. An early version said "GPT-four" |
| ✅ → 🔹 | dropped | Decorative symbols are removed, but × and ≥ are spoken and é is kept. This step runs in the narration pipeline that took over production, not in the rewriter below |

The order matters as much as the rules. Dates go before bare years, or the year in "2026-07-19" is read first. Currency goes before plain numbers, or the symbol is left stranded. Domains go before numbers, because the number step writes "a.m." and the domain step must never see it. The rewriter is [tts-bench/speakable.py](tts-bench/speakable.py), with 183 tests in [tests/test_speakable.py](tests/test_speakable.py). It uses only the Python standard library.

## Engines not sampled here

- **F5-TTS** was intelligible but carries a non-commercial licence, so it could never ship. Its samples are not published.
- **Fish s2-pro** returned a well-formed audio file of 47 seconds of background noise for an ordinary sentence ([F50](FINDINGS.md#f50)). Its licence was also unresolved.
- **Qwen3-TTS** offers only male English voices, and the narrator brief was a female voice.
- **MegaTTS3** cannot clone a supplied recording, because its encoder is withheld ([F52](FINDINGS.md#f52)). **Zonos** never finished loading on this graphics chip ([F53](FINDINGS.md#f53)).

## Licences and attribution

- Voice references 01 and 04, and the cloned voices in 02, 03 and 05 to 07 and 09, derive from the CSTR VCTK Corpus (Yamagishi, Veaux and MacDonald, University of Edinburgh), licensed CC BY 4.0.
- Engines: Chatterbox (Resemble AI) MIT; VoxCPM2 (OpenBMB) Apache-2.0; Kokoro-82M Apache-2.0; CosyVoice3 (FunAudioLLM) Apache-2.0.
- The full engine evidence, with throughput and failure analysis, is in [tts-bench/](tts-bench/) and findings F47 to F56.
