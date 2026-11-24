<!--
# File: results/e173-results.md
# Purpose: Results of E173 - three local music models (YuE2, MiniMax Music 3, ACE-Step 1.5) on audio.cpp Vulkan.
# Project: sparkbench | Date: 2026-11-24
#
# Overview: Scores results/e173-prereg.md (frozen by A1, A2 declared before unsealing) against results/e173/renders.tsv
# (15 renders, 2026-11-23 21:27-00:50Z), results/e173/score.json (whisper.cpp large-v3-turbo on CPU) and the owner's
# listening answers (results/e173/owner-answers-1.txt, owner-notes-1.md). YuE2 is an internal-only arm (CC BY-NC).
-->

# E173 RESULTS - local music models

## In plain English

All three music models run on this box and finish a two-minute song, but none of them produced music the owner
liked: he "didn't really like the music style of any of them". Judged on sound quality and clear words instead, he
would play ACE-Step on three of five songs, YuE2 on three (internal only: its licence bars commercial use) and MiniMax
on one (one MiniMax take would not play in the page). ACE-Step is also by far the fastest: a two-minute song in about
95 seconds, where MiniMax takes about half an hour. By the automatic lyric check the three are close; every model
dropped about half of the key phrases. If a music model goes forward to the SparkForge video experiment, it is
ACE-Step, and the open question is style, not engine.

## Measured

| Field | YuE2 | MiniMax Music 3 | ACE-Step 1.5 |
|---|---|---|---|
| renders rc 0 | 5/5 | 5/5 | 5/5 |
| `rtf_median` (wall / audio) | 2.168 | 18.133 | **0.787** |
| audio length, s | 102-183 | 78-150 | 120 (fixed) |
| `peak_gtt_mib` over baseline | 7,087 | 17,439 | 11,325 |
| `wer_median` (lyrics) | 0.184 | 0.242 | **0.179** |
| `key_phrases_heard` | 6/13 | 6/13 | 6/13 |
| `owner_use_yes` ("would play to a room") | 3/5 | 1/5 (of 4 heard) | 3/5 |
| `owner_rank1` | void (A2) | void | void |

`load_s` was not captured by the runner (renders.tsv has no load field); not scored. WER per render and transcripts:
`results/e173/score.out`, `results/e173/renders/*.txt`.

## Predictions

- **P1 HELD.** All three render on Vulkan, the shared backend (spike 2026-11-23; MiniMax hangs on HIP).
- **P2 HELD.** ACE-Step 0.787 < YuE2 2.168 and MiniMax 18.133.
- **P3 HELD.** MiniMax 18.133 > 1.389; YuE2 2.168 > 0.2688.
- **P4 FALSIFIED.** MiniMax's WER median 0.242 is the highest, not the lowest. One MiniMax transcript (S2, 0.979) is a
  whisper repetition loop ("If in love, man" x N), a transcriber failure on music, not evidence about the model; without
  it MiniMax's median would be 0.202, still above ACE-Step 0.179. ACE-Step vs YuE2 (0.179 vs 0.184) is inside the
  noise of sung-lyric WER: call it a tie.
- **P5 UNSCORED** (A2): no ranks, because the page's rank dropdown did not work for the owner.
- **P6 HELD.** Max peak 17,439 MiB < 32,768.

## Owner listening (results/e173/owner-notes-1.md)

- Judged mainly on **sound quality and words**, not style; **liked the style of none**.
- Room ticks per song (unsealed): S1 ACE-Step; S2 ACE-Step, YuE2; S3 all three; S4 YuE2; S5 none.
- "They got better as they went on down": page order was fixed S1-S5, so order effect and song differences are
  confounded for one listener.
- S4 take C (MiniMax) failed to play in the viewer; the file decodes cleanly and its published hash matches.

## Deviations and open items

- Rank dropdown defect in the listening page: fix and browser-test before any second round; shuffle song order too.
- Key-phrase misses (21 across 15 renders) were to get a mandatory human listen (prereg); NOT done - the owner's
  listen was whole-song. Listed in `score.out`.
- MiniMax S2 transcript is a whisper failure; a second transcriber or a human listen would be needed to score it.
- YuE2 outputs are not publishable (CC BY-NC); nothing from that arm goes into Local-AI audio.
