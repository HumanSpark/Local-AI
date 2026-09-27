#!/usr/bin/env python3
# File: build_claims_json.py
# Purpose: Emit local-ai-claims.json - the machine-readable claims + chart-series registry the
#          WordPress /local-ai/ build reads (so it absorbs release bumps by re-reading one file).
# Project: sparkbench | Date: 2026-07-12
#
# Overview: Two sections. `claims` - one entry per claim ID in claims.yml, carrying the CURRENT
# canonical value (post-Release-2.0: FX 0.87617360, sustained-rate cost EUR 0.09/1M, etc.), its
# unit, confidence interval, primary source_file, status, and a one-line UK-English description.
# `charts` - the underlying series for the five report charts (same numbers as the rendered PNGs,
# straight from tools/build_charts.py). Stable key names across releases (never rename `id`).
# Regenerate every release; deliver alongside the release zips to the Alchemy sparkbench folder.
# Usage: build_claims_json.py [out.json]  (default: results/local-ai-claims.json)

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path("/home/agent-spark/sparkbench")

# One entry per claim ID in claims.yml. Values reconciled to the frozen Release 2.0 report /
# cost_model.py / cloud-pricing.yml (FX 0.87617360). CI as [low, high] where measured.
CLAIMS = [
    dict(id="C-LOCAL-SUMM-001", value=93.3, unit="percent", confidence_interval=[78.7, 98.2],
         source_file="results/experiments.md", status="confirmed",
         description="Local workhorse (Qwen3-30B-A3B) scored 93.3% on the document-summarisation suite."),
    dict(id="C-LOCAL-IF-001", value=87.5, unit="percent", confidence_interval=[69.0, 95.7],
         source_file="results/experiments.md", status="confirmed",
         description="Local workhorse scored 87.5% on the structured instruction-following suite."),
    dict(id="C-LOCAL-SUMM-4B", value=96.7, unit="percent", confidence_interval=[83.3, 99.4],
         source_file="results/experiments.md", status="confirmed",
         description="The small local model (Qwen3-4B) scored 96.7% on the summarisation suite."),
    dict(id="C-CLOUD-SUMM-FRONTIER", value=90.0, unit="percent", confidence_interval=None,
         source_file="results/experiments.md", status="confirmed",
         description="Frontier cloud (gpt-5.6-sol) scored 90.0% on the summarisation suite; cheap cloud (gpt-5.4-mini) 93.3%."),
    dict(id="C-CLOUD-IF-FRONTIER", value=75.0, unit="percent", confidence_interval=None,
         source_file="results/experiments.md", status="confirmed",
         description="Frontier cloud (gpt-5.6-sol) scored 75.0% on instruction-following; cheap cloud (gpt-5.4-mini) 100%."),
    dict(id="C-CAPABILITY-PARITY-001", value=None, unit="qualitative", confidence_interval=None,
         source_file="results/frontier-eval.md", status="confirmed",
         description="On fact-checkable document benchmarks (summarisation, extraction) local was competitive with the tested cloud comparator; a harder send-readiness test tells the fuller story (see C-QUALITY-SENDREADY-001)."),
    dict(id="C-CAPABILITY-SPEED-001", value=92.3, unit="tokens_per_second", confidence_interval=[91.1, 93.5],
         source_file="results/experiments.md", status="confirmed",
         alias_of="C-SPEED-WORKHORSE-P1",
         description="Workhorse fresh-context generation speed is about 92 tokens per second. (Alias of C-SPEED-WORKHORSE-P1 - same fact, older scaffold ID.)"),
    dict(id="C-SPEED-WORKHORSE-P1", value=92.3, unit="tokens_per_second", confidence_interval=[91.1, 93.5],
         source_file="results/experiments.md", status="confirmed",
         description="Workhorse fresh-context generation speed is about 92 tokens per second (baseline)."),
    dict(id="C-CAPABILITY-TRANSCRIPTION-001", value=28.0, unit="times_real_time", confidence_interval=None,
         source_file="results/capability-probes.md", status="confirmed",
         description="Meeting transcription (Whisper) runs at about 28 times real time - a one-hour meeting in roughly two minutes."),
    dict(id="C-COST-MARGINAL-001", value=0.09, unit="eur_per_1m_output_tokens", confidence_interval=[0.04, 0.09],
         source_file="results/experiments.md", status="confirmed",
         alias_of="C-COST-MARGINAL-P1",
         description="Marginal electricity cost to generate 1M output tokens is about EUR 0.09 single-user, falling to about EUR 0.04 batched across sixteen users. (Alias of C-COST-MARGINAL-P1 - same fact, older scaffold ID.)"),
    dict(id="C-COST-MARGINAL-P1", value=0.09, unit="eur_per_1m_output_tokens", confidence_interval=[0.04, 0.09],
         source_file="results/experiments.md", status="confirmed",
         description="Marginal electricity cost per 1M output tokens: about EUR 0.09 single-user, EUR 0.04 batched (sustained 72.8 t/s basis)."),
    dict(id="C-HARDWARE-SPEC-001", value=3680, unit="eur_cash_outlay", confidence_interval=None,
         source_file="manifests/MANIFEST.md", status="confirmed",
         description="Hardware is a GMKtec EVO-X2 (Ryzen AI Max+ 395, 128 GB unified memory): EUR 2,960 net, about EUR 3,680 cash outlay including Irish import VAT."),
    dict(id="C-COMPRESS-MMLU-FLAT", value=None, unit="qualitative", confidence_interval=None,
         source_file="reports/integrated-technical-results-v2.md", status="confirmed",
         description="Knowledge (MMLU) stays flat within confidence intervals from the 8-bit baseline down to about 2-bit; the first clear drop is at 1-bit ternary."),
    dict(id="C-COMPRESS-SUMM-FLAT", value=None, unit="qualitative", confidence_interval=None,
         source_file="reports/integrated-technical-results-v2.md", status="confirmed",
         description="Document-task accuracy is unchanged across every quantisation rung down to the ternary floor (suite ceiling)."),
    dict(id="C-COMPRESS-SPEED-CURVE", value=1.7, unit="times_speedup", confidence_interval=None,
         source_file="reports/integrated-technical-results-v2.md", status="confirmed",
         description="A Q2-class build generates about 1.7 times faster than the 8-bit baseline (61 to 106 tokens/sec) at one-third the file size."),
    dict(id="C-LONGCTX-USABLE", value=48000, unit="tokens", confidence_interval=None,
         source_file="results/experiments.md", status="confirmed",
         description="Interactive long-context ceiling is about 48,000 tokens on the Vulkan stack, extending to 64,000 on a ROCm serving build."),
    dict(id="C-LONGCTX-ACCURACY", value=100.0, unit="percent_retrieval_accuracy", confidence_interval=None,
         source_file="results/experiments.md", status="confirmed",
         description="Retrieval accuracy holds (6 of 6 needle probes) out to 80,000-plus tokens; beyond the interactive ceiling the constraint is speed, not correctness."),
    dict(id="C-REASONING-TOKEN-TAX-CLOUD", value=3.5, unit="times_token_overhead", confidence_interval=None,
         source_file="results/experiments.md", status="confirmed",
         description="Reasoning-emitter models generate roughly 3 to 12 times more tokens, for lower quality on structured output."),
    dict(id="C-REASONING-TOKEN-TAX-LOCAL", value=None, unit="qualitative", confidence_interval=None,
         source_file="results/experiments.md", status="confirmed",
         description="Local reasoning-emitter models pay the same 3-12x token tax and are not suited to structured document work."),
    dict(id="C-RELIABILITY-12K-P1", value=83.0, unit="percent", confidence_interval=None,
         source_file="docs/FINDINGS.md", status="confirmed",
         description="Every model in the fleet scored at least 83% on 12,000-token document work; accuracy holds even on the smaller models."),
    dict(id="C-CAPACITY-TIERING-001", value=None, unit="qualitative", confidence_interval=None,
         source_file="docs/FINDINGS.md", status="confirmed",
         description="Everyday models (4-30 GB) are safe under all tested load; models over about 60 GB can deadlock under heavy concurrent disk I/O."),
    dict(id="C-OP-GUIDANCE-ROCM-LEVER", value=None, unit="operational_guidance", confidence_interval=None,
         source_file="docs/FINDINGS.md", status="confirmed",
         description="A ROCm serving build lifts the interactive long-context ceiling from 48,000 to 64,000 tokens (64K first answer 3m17s against 6m43s on Vulkan), measured just after the data freeze."),
    # CORRECTED 2026-07-17 (F43): the 2.66x was measured with all 16 streams running the SAME prompt,
    # which lets a MoE batch share expert loads. With DISTINCT users the curve peaks at ~4 and declines.
    # The small-team conclusion SURVIVES and is now measured rather than extrapolated: 4 concurrent
    # users is the box's best point (121.35 t/s aggregate, ~39 t/s each - faster than reading speed).
    dict(id="C-CONCURRENCY-SMALL-TEAM-P1", value=None, unit="qualitative", confidence_interval=None,
         source_file="docs/FINDINGS.md", status="confirmed",
         description="One box comfortably serves a small team of 3-5 with intermittent use, and about four concurrent users is its best point: aggregate throughput peaks there at roughly 121 tokens per second, giving each user about 39 tokens per second - faster than anyone reads. Beyond that it does not keep improving; at sixteen concurrent users aggregate FALLS to about 109 tokens per second and each user drops to about 8. A single user is unaffected."),

    # --- Promoted from findings/charts/cost model (2026-07-12 promotion pass) ---
    dict(id="C-ARCH-MOE-ADVANTAGE", value=8.5, unit="times_faster_generation", confidence_interval=None,
         source_file="reports/integrated-technical-results-v2.md", status="confirmed",
         description="At the same size, quantisation and model family, the mixture-of-experts architecture generates about 8.5 times faster (and prefills about 5.8 times faster) than the dense equivalent - architecture matters more than size."),
    dict(id="C-PREFILL-ROCM-VULKAN", value=8.08, unit="times_faster_prefill", confidence_interval=None,
         source_file="reports/integrated-technical-results-v2.md", status="confirmed",
         description="On a ROCm serving build, prompt processing (prefill) reaches about 8.08 times the Vulkan speed at depth - the lever behind the extended interactive long-context ceiling."),
    # CORRECTED 2026-07-17 (F43): value 2.66 -> 1.53. The 2.66x is real but is a SAME-QUESTION best
    # case (all 16 streams ran one prompt); with sixteen users asking sixteen different questions the
    # measured scaling is 1.53x and the curve knees at ~4. MoE-specific: dense models show no penalty.
    dict(id="C-CONCURRENCY-MOE-SCALING", value=1.53, unit="times_throughput_1_to_16_distinct_users", confidence_interval=None,
         source_file="docs/FINDINGS.md", status="confirmed",
         description="With sixteen people asking sixteen different questions at once, the MoE workhorse delivers about 1.53 times the throughput of a single user - not the 2.66 times a same-question benchmark suggests. Mixture-of-Experts models route each token to a few specialists, so when concurrent requests differ the machine must fetch far more of the model per step. Conventional dense models do not behave this way (no measurable penalty), and a single user is unaffected either way."),
    dict(id="C-COMPRESS-SIZE-RANGE", value=30.25, unit="gib_8bit_baseline_to_7p54_ternary", confidence_interval=None,
         source_file="reports/integrated-technical-results-v2.md", status="confirmed",
         description="The workhorse file shrinks from 30.25 GiB at the 8-bit baseline (Q8_0) to 10.49 GiB at Q2-class and 7.54 GiB at 1-bit ternary."),
    dict(id="C-COST-BREAKEVEN-FRONTIER", value=81, unit="tasks_per_day", confidence_interval=None,
         source_file="tools/cost_model.py", status="confirmed",
         description="The box pays back on running cost only against the frontier tier, above about 81 tasks per day; never against the cheap or EU cloud tiers at a small firm's volume."),
    dict(id="C-COST-PER-TASK-RATIO", value=338, unit="times_cheaper_than_frontier_per_task", confidence_interval=None,
         source_file="tools/cost_model.py", status="confirmed",
         description="Per document task, local electricity is about 338 times cheaper than the frontier cloud tier, 51 times cheaper than cheap cloud, and 32 times cheaper than EU cloud."),
    dict(id="C-COST-TCO-3YEAR", value=3683, unit="eur_three_year_local", confidence_interval=None,
         source_file="tools/cost_model.py", status="confirmed",
         description="Three-year total cost of ownership: about EUR 3,683 local (hardware-dominated) against about EUR 85 (EU) to EUR 907 (frontier) for cloud at roughly 5,000 document tasks a year."),
    dict(id="C-POWER-DRAW-P1", value=81, unit="watts_package_single_user", confidence_interval=None,
         source_file="reports/integrated-technical-results-v2.md", status="confirmed",
         description="Measured package power: about 4 W idle, 81 W under single-user inference, 83 W at sixteen concurrent users, with peaks of 93-107 W; wall draw is roughly 10-25 W higher (estimated, not plug-meter measured)."),
    dict(id="C-CLOUD-CHEAP-IF-BEST", value=100.0, unit="percent_instruction_following", confidence_interval=None,
         source_file="results/experiments.md", status="confirmed",
         description="The cheap cloud tier (gpt-5.4-mini) scored 100% on the instruction-following suite, ahead of the frontier's 75% - but this suite is a saturated format-compliance floor that does not separate capable models; on real drafting the frontier (gpt-5.6-sol) is clearly best. Read as 'the cheap tier clears the floor', not 'the cheap tier is better'."),
    dict(id="C-REASONING-NONRECOVERY", value=None, unit="qualitative", confidence_interval=None,
         source_file="results/experiments.md", status="confirmed",
         description="Reasoning-emitter models did not recover to direct-model performance on structured output even at a generous 8,192-token budget - a pre-registered prediction that missed, published as measured."),
    dict(id="C-LONGCTX-FIRST-ANSWER", value=206, unit="seconds_first_answer_at_48k", confidence_interval=None,
         source_file="results/experiments.md", status="confirmed",
         description="First-answer latency climbs with document length: about 30 seconds at 16K tokens, 95 seconds at 32K, 3.5 minutes at 48K, and 14 minutes at 80K; follow-up questions return in seconds."),
    dict(id="C-CODING-DEFAULT", value=None, unit="operational_guidance", confidence_interval=None,
         source_file="docs/plans/2026-07-12-coding-screen-10-realproject-results.md", status="confirmed",
         description="For local coding, Qwen3-Coder-30B is the recommended default (GLM-4.7-Flash as fallback); the document-suite workhorse is not suited to agentic coding - benchmark strength did not transfer."),
    # --- v3.0: the output-QUALITY workstream (F34, F35, F37) ---
    # source_file was results/real-quality/eval-pilot.md, which never existed (a mashup of the
    # results/real-quality/ evidence dir and the unrelated results/eval-pilot.md). These are F34
    # claims; F34 is established in FINDINGS.md and points on to results/real-quality/. Matches its
    # sibling C-QUALITY-CEILING-001. Caught 2026-07-16 when the completeness gate stopped accepting
    # a citation just because some file of that basename existed elsewhere.
    dict(id="C-QUALITY-SENDREADY-001", value=3.0, unit="send_readiness_1_to_5", confidence_interval=None,
         source_file="docs/FINDINGS.md", status="confirmed",
         description="On a real-work send-readiness test (would a professional send the draft, graded 1-5 by an independent frontier model over ten solicitor/accountant tasks), the best local models rate about 3.0 - a usable first draft that needs a real edit - against the frontier's about 4.4. Getting facts right on a benchmark is not the same as being send-ready."),
    dict(id="C-QUALITY-GROUNDED-001", value=None, unit="qualitative", confidence_interval=None,
         source_file="docs/FINDINGS.md", status="confirmed",  # was the same never-existent path; see above
         description="Local output is strongest - close to send-ready, facts exact - on grounded tasks like extracting terms and summarising a document, which is precisely the confidential document work the box is for; it is weakest on open-ended drafting, where faithfulness is the limit and human review catches it."),
    dict(id="C-QUALITY-CEILING-001", value=None, unit="qualitative", confidence_interval=None,
         source_file="docs/FINDINGS.md", status="confirmed",
         description="No stock model or training-free technique closed the send-readiness gap: bigger models, reasoning models, the model checking its own work, showing it good examples in the prompt, and pooling several models all left local drafting at about the same level. Raw capability, not configuration, is the limit."),
    dict(id="C-FINETUNE-VOICE-001", value=None, unit="qualitative", confidence_interval=None,
         source_file="docs/FINDINGS.md", status="confirmed",
         description="A house-style fine-tune trained on the box on your own examples reliably teaches the model your firm's voice and register (a consistent tone lift across two runs, no loss of factual faithfulness), but does not raise the send-readiness score itself, and a five-times-larger training set did not change that. It is a voice-adaptation lever, not a way to remove the edit."),
    dict(id="C-TRAINING-ONBOX-001", value=None, unit="qualitative", confidence_interval=None,
         source_file="docs/FINDINGS.md", status="confirmed",
         description="The box can train a model, not only run one: a house-style adapter was trained end-to-end on the machine itself (generate examples, train, serve) with no cloud step and nothing leaving the building - the strongest form of owning your capability."),
    dict(id="C-TOOLUSE-DOC-001", value=91, unit="percent_correct_tool_call", confidence_interval=None,
         source_file="docs/FINDINGS.md", status="confirmed",
         description="Given office tools (create a Word document, send an email, add a reminder, look up a client), the workhorse (Qwen3-30B-Instruct) called the correct tool on 91% of a broad 22-task suite (5 runs each) with zero malformed calls, producing real .docx files, and correctly answered plain questions in text without over-calling a tool. Tool use / document creation is real and reliable on the right model. (F38, experiments E32-E33.)"),
    dict(id="C-TOOLUSE-SERVING-001", value=None, unit="qualitative", confidence_interval=None,
         source_file="docs/FINDINGS.md", status="confirmed",
         description="Out-of-the-box tool-use support is serving-config dependent, not just model dependent: on the same llama.cpp build the workhorse and gpt-oss-20b emit clean tool calls immediately, Mistral-Small-3.1 silently refuses until supplied a tool template its GGUF does not ship, and Qwen3-Coder leaks its native call format as unparseable text about 5% of the time. Choose a tool-use model by measured parse-reliability on your own stack, not by reputation. (F38, E33.)"),
    dict(id="C-TOOLUSE-CONDITIONAL-001", value=None, unit="qualitative", confidence_interval=None,
         source_file="docs/FINDINGS.md", status="confirmed",
         description="Reasoning inside a tool call is unreliable for most local models: told to mark a document urgent only when a balance exceeded a threshold, the Qwen family and gpt-oss applied the flag unconditionally; Mistral was the exception. The mechanical step (make the file, send the message) is dependable; the judgement inside it still needs a human check. (F38, E33.)"),
    # --- r4.6: the meeting-intelligence workstream (transcription accuracy, silence, speaker attribution) ---
    dict(id="C-TRANSCRIPTION-WER-001", value=2.40, unit="percent_word_error_rate", confidence_interval=None,
         source_file="results/transcription/e45-true-wer.md", status="confirmed",
         description="On the standard read-speech benchmark (LibriSpeech test-clean, human transcripts), local Whisper large-v3-turbo transcribes at a 2.40% word error rate, matching the published figure for the model - which validates the measurement harness as well as the number. The smaller model is worse (3.35%), and the larger model is about 28% more accurate on real meeting audio too: our own hypothesis that smaller models might transcribe better was tested and refuted. This is clean read speech, the easy case; it is the model comparison and a harness check, not a meeting-accuracy figure. (F45, E42/E45.)"),
    dict(id="C-TRANSCRIPTION-SILENCE-VAD-001", value=None, unit="operational_guidance", confidence_interval=None,
         source_file="docs/FINDINGS.md", status="confirmed",
         description="Voice-activity detection is mandatory, not optional, for Whisper transcription: without it the model fabricates about two invented utterances per minute of silence (97% of them the phrase 'Thank you.'), and voice-activity detection removes them completely (zero across 72 test conditions). This is a well-documented failure mode in the literature, reproduced here, not a discovery. One reframing is ours: counted by volume the smaller model hallucinates more, but counted by HARM the larger model is about five times worse, because it invents grammatical speech a reader cannot distinguish from a real utterance while the smaller model labels the gap as blank. (F44, E41.)"),
    dict(id="C-TARGET-SPEAKER-001", value=97.2, unit="percent_segment_attribution", confidence_interval=None,
         source_file="results/diarisation/e50-target-speaker.md", status="confirmed",
         description="Asking 'is this the host speaking or someone else' - a binary question - is far more tractable than full speaker diarisation and is what meeting intelligence actually needs. From a single ~4-minute voiceprint of the host, the system tags 97.2% of transcript lines correctly as host-versus-other across four real calls (a separate enrollment recording, so genuine cross-session performance). The difficulty inverts against general diarisation: more people in the room makes the binary question easier, not harder. General diarisation is the harder problem and a specialist tool (pyannote) still beats ours roughly three-to-one on it; the reframe to the host-versus-other question is what makes the product work. (F46, E50.)"),
    dict(id="C-DIARISATION-FARFIELD-001", value=None, unit="qualitative", confidence_interval=None,
         source_file="results/diarisation/e44-vad-fix.md", status="confirmed",
         description="An on-prem meeting box does not need a headset per person: on the standard meeting corpus a single distant table microphone came within about one diarisation-error point of close-talk headsets (21.1% versus 20.2%), against a predicted eight-point penalty. Replacing a naive energy gate with a real voice-activity detector was what closed most of the gap, nearly halving the error. (F46, E44.)"),
    # r5.1 - vendor and community claims tested on the box (E138, E139, E143, E145, E146; F159, F164, F165-F171)
    dict(id="C-CLAIM-BONSAI-SPEED-001", value=34.16, unit="tokens_per_second_decode", confidence_interval=None,
         source_file="results/e138-results.md", status="confirmed",
         description="A public '~73 tok/s on Strix Halo' for Ternary Bonsai 2 27B does not reproduce: 34.16 tok/s was the best of nine configurations (PQ2_0 plus a DFlash2 drafter, code prompt), and the claim's own 10.1 GB memory figure matches the PTQ1_0 configuration, which decodes at 3.63 tok/s on this Vulkan stack. Plain Bonsai runs 22.22 tok/s in 8.07 GiB against the incumbent 27B's 12.33 in 16.78 GiB; answer quality was not measured, so no swap is recommended on speed alone."),
    dict(id="C-CLAIM-HALOGEN-PREFILL-001", value=1152.01, unit="tokens_per_second_prefill_32k", confidence_interval=None,
         source_file="results/e139-results.md", status="confirmed",
         description="Halogen's published '~1,424 tok/s prefill at 32K' for Qwen3.8-Flash-Next measures 1,152 tok/s here (median of 3), scored reproduced-conditionally against a 1,000-1,210 band that allowed for this box's IOMMU mode; mainline llama.cpp on our GGUF does 216.5 tok/s, so a 32K request takes 33 s on Halogen and 162 s on llama.cpp. Its speculative decoding was byte-identical to serial on 4 of 4 prompts. Halogen could not serve our GGUF beside the resident TTS service: it repacks the file into 70 GiB of host RAM and was stopped twice by the 12 GiB memory guard."),
    dict(id="C-CLAIM-ATLAS-MLPERF-001", value=9307, unit="mean_turn_latency_ms", confidence_interval=None,
         source_file="results/e146-results.md", status="confirmed",
         description="On MLCommons' own edge-agentic harness (Qwen3.6-27B, 206 of 1,007 turns, single stream) Atlas took 9,307 ms per turn (Atlas HEAD plus a one-line patch) and 9,453 ms (the MLPerf entry's shipped source) against 12,863 ms for the llama.cpp reference: paired ratios 0.724 and 0.735 on the same turns, inline accuracy within 0.03. The entry's published 7,059 ms was not reproduced (1.32-1.34x). The reference runs no speculation; with a DFlash drafter added and nothing else changed (E147), llama.cpp took 7,775 ms per turn at identical accuracy, and both Atlas builds were 1.20-1.22x slower than that open configuration (F172). Atlas's own DFlash mode with the same drafter lineage (E148) took 22,898 ms per turn, 2.46x its MTP mode, because the drafter accepted 0.064 tokens per 15-draft step past 4K context; the MLPerf-era source cannot serve that mode on HIP (F175)."),
    dict(id="C-CLAIM-ATLAS-DETERMINISM-001", value=3, unit="distinct_outputs_of_10_identical_greedy_requests", confidence_interval=None,
         source_file="results/e146-results.md", status="confirmed",
         description="Atlas (HEAD 2d1aab8, Qwen3.8-27B NVFP4, MTP K=4) returned 3 distinct outputs to 10 identical temperature-0 requests in one process; llama.cpp returned 1 distinct output to the same test, with and without a drafter. Atlas's README decode claim of 28.3-28.6 tok/s on code prompts measured 27.18, confirmed."),
    dict(id="C-CODING-RECOMMENDED-TIE-001", value=None, unit="qualitative", confidence_interval=None,
         source_file="results/e145-results.md", status="confirmed",
         description="Seven coding models recommended by a Strix Halo chat and a comparison widget (Qwen3.8-27B, Qwen3.8-Flash-Next, two quants of Qwen3.6-35B-A3B, Ornith 1.0 and 1.5, Qwen3.6-27B) tie with the incumbent Qwen3-Coder through Aider on three real repo tasks: 5 to 7 passes of 9 for every model against a pre-registered band of 4 for a real difference, with the incumbent 2x to 10x faster per attempt set. The widget's speed order held (its 'faster' option is 39% faster; it said 42%) and its 27B penalty did not (4.7x, it said 2.09x). Every failure on the task the incumbent passes carries only the seed diff: the other models' edits never reached the file (F171)."),
]

CHARTS = {
    "generation-speed-vs-depth": {
        "type": "line", "x_label": "context depth (tokens)", "y_label": "generation speed (tokens/sec)",
        "annotations": ["instant threshold at 70 tokens/sec"],
        "series": [
            {"name": "Qwen3-30B-A3B (workhorse, MoE)", "points": [{"x": x, "y": y} for x, y in zip(
                [0, 2048, 4096, 8192, 16384, 32768, 65536, 98304], [92.28, 82.35, 76.30, 67.06, 53.21, 38.32, 24.69, 18.40])]},
            {"name": "Qwen3.6-35B (hybrid)", "points": [{"x": x, "y": y} for x, y in zip(
                [0, 2048, 4096, 8192, 16384, 32768], [58.71, 57.08, 56.53, 55.14, 52.47, 47.87])]},
            {"name": "GLM-4.7-Flash (MLA)", "points": [{"x": x, "y": y} for x, y in zip(
                [0, 4096, 8192, 16384, 32768], [70.93, 57.12, 50.50, 39.21, 27.91])]},
            {"name": "gpt-oss-20b (SWA)", "points": [{"x": x, "y": y} for x, y in zip(
                [0, 4096, 8192, 16384, 32768], [75.22, 71.24, 67.51, 63.57, 56.08])]},
        ],
    },
    "moe-vs-dense-architecture": {
        "type": "bar", "y_label": "throughput (tokens/sec)",
        "note": "same size, same quant, same family - only the architecture differs (8.5x generation, 5.8x prefill)",
        "series": [
            {"name": "generation (tg128)", "bars": [
                {"category": "Qwen3-30B-A3B (MoE)", "value": 92.83}, {"category": "Qwen3-32B (dense)", "value": 10.89}]},
            {"name": "prefill (pp512)", "bars": [
                {"category": "Qwen3-30B-A3B (MoE)", "value": 1137.67}, {"category": "Qwen3-32B (dense)", "value": 198.20}]},
        ],
    },
    "cost-per-1m-tokens": {
        "type": "bar", "x_label": "EUR per 1M output tokens (log scale)", "scale": "log",
        "note": "output rate only; cloud-pricing.yml 2026-07-12, FX 0.87617360; electricity EUR 0.298/kWh",
        "bars": [
            {"category": "Local - 16 users (electricity)", "value": 0.04},
            {"category": "Local - 1 user (electricity)", "value": 0.09},
            {"category": "Mistral Large 3 (EU)", "value": 1.31},
            {"category": "gpt-5.4-mini (cheap)", "value": 3.94},
            {"category": "gpt-5.6-sol (frontier)", "value": 26.29},
        ],
    },
    "concurrency-scaling": {
        "type": "line", "x_label": "concurrent slots (users)", "y_label": "aggregate throughput (tokens/sec)",
        "series": [
            # Both curves shipped deliberately (F43): the same-question line is what a standard
            # concurrency benchmark measures; the distinct-users line is what a real team gets.
            # Showing only the first would overstate fleet capacity by 1.78x at 16 users.
            {"name": "Qwen3-30B-A3B (MoE) - 16 users asking the SAME question", "points": [{"x": x, "y": y} for x, y in zip(
                [1, 4, 16], [72.85, 137.08, 193.49])]},
            {"name": "Qwen3-30B-A3B (MoE) - 16 users asking DIFFERENT questions (real load)", "points": [{"x": x, "y": y} for x, y in zip(
                [1, 4, 16], [71.59, 121.35, 109.40])]},
            {"name": "gpt-oss-20b - knees at ~4", "points": [{"x": x, "y": y} for x, y in zip(
                [1, 4, 16], [59.86, 101.32, 108.99])]},
            {"name": "GLM-4.7-Flash (MLA) - anti-scales 0.70x", "points": [{"x": x, "y": y} for x, y in zip(
                [1, 4, 16], [54.07, 45.45, 38.06])]},
        ],
    },
    "vulkan-vs-rocm": {
        "type": "line", "x_label": "context depth (tokens)", "y_label": "prefill speed pp512 (tokens/sec, log)", "scale": "log",
        "note": "pure-MoE prefill; ROCm reaches 8.08x Vulkan at depth",
        "series": [
            {"name": "Vulkan", "points": [{"x": x, "y": y} for x, y in zip(
                [0, 8192, 16384, 32768, 65536, 98304], [1140.72, 561.16, 346.59, 180.77, 53.39, 16.57])]},
            {"name": "ROCm", "points": [{"x": x, "y": y} for x, y in zip(
                [0, 8192, 16384, 32768, 65536, 98304], [1205.15, 752.09, 528.11, 323.68, 189.53, 133.86])]},
        ],
    },
}

META = {
    "schema_version": "1.0",
    "release": "4.0",
    "run_window": "3-17 July 2026",
    "data_freeze": "2026-07-17",
    "fx_usd_to_eur": 0.87617360,
    "electricity_eur_per_kwh": 0.298,
    "note": "Canonical machine-readable registry for the Local AI resource. Release 4.0 is the data-package architecture (sparkbench ships evidence + FINDINGS + claims registry, not HTML); content carries the tool-use benchmark (C-TOOLUSE-*, F38) and the output-QUALITY workstream forward from 3.1. r4.6 adds the meeting-intelligence workstream (C-TRANSCRIPTION-*, C-TARGET-SPEAKER-*, C-DIARISATION-*; F44-F46) - transcription accuracy, silence hallucination, and host-versus-other speaker attribution, all measured 2026-07-17. Values reconciled to tools/cost_model.py and results/deep-eval/cloud-pricing.yml. Key names are stable across releases.",
    "alias_convention": "An entry with an 'alias_of' field is a duplicate of the same fact under an older scaffold ID; pick the entry WITHOUT 'alias_of' as canonical per fact. C-CAPABILITY-SPEED-001 aliases C-SPEED-WORKHORSE-P1; C-COST-MARGINAL-001 aliases C-COST-MARGINAL-P1.",
}


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "results/local-ai-claims.json"
    doc = {"meta": META, "claims": CLAIMS, "charts": CHARTS}
    out.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {out}  ({len(CLAIMS)} claims, {len(CHARTS)} charts, {out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
