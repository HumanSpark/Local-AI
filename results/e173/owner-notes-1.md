<!--
# File: results/e173/owner-notes-1.md
# Purpose: The owner's comments on the E173 blind listening gate, recorded as given, plus the checks run on them.
# Project: sparkbench | Date: 2026-11-24
#
# Overview: Received in the session 2026-11-24 ~01:25Z, AFTER the key was opened (A2). Quoted verbatim.
-->

## Owner, verbatim

> I wasn't able to use the ranking drop down, so I just used the room.
> I just want to note that I didn't really like the music style of any of them. They got better as they went on
> down, and I did get an error when I tried to play, I think the third one of the fourth set.

> I was ranking the sound quality and words a bit more than the actual style of music.

## What follows from it

1. **No ranks because the page's rank dropdown did not work for him** - a defect in the listening page
   (tools/e173_listening_template.html / build_e173_listening.py), not a choice. Cause not established; it was not
   reproduced here. Fix and test the control in a browser before the next listening gate.
2. **Style: he did not like the music style of any take, and judged the room ticks on SOUND QUALITY AND WORDS more
   than on style.** So the room ticks read as "clean enough and intelligible enough to play", which makes them a human
   check on the same axis as the WER / key-phrase scores, not a taste verdict. No arm met his taste in style; the
   style prompts (frozen in prompts.json) are a separate lever from the model and were not varied in this round.
3. **"They got better as they went on down":** the songs later on the page sounded better to him. Page order was fixed
   S1 to S5, the same for every listener, so an order effect (listener warming up) and real song differences cannot
   be told apart from one listener.
4. **Playback error on S4 take C = MiniMax S4.** The file is intact: ffmpeg decodes it with no error (89.76 s, 192 kbps,
   stereo) and the published sha256 matches the local one (45b7d610...). The failure was in the viewer, not the audio,
   and was not reproduced. Consequence: MiniMax could not be ticked for S4, so `MM.owner_use_yes` = 1/5 is out of 4
   songs actually heard, not 5.
