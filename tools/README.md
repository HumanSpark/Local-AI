# tools/

Every file in this folder with its own one-line description (a document's title, or a script's Purpose line). A blank means the file does not state one.

| File | Description |
|---|---|
| [LICENSE](LICENSE) |  |
| [adjudicate_dispute.py](adjudicate_dispute.py) | Decide acoustically whether a reference transcript mis-attributed a long monologue block. |
| [aider-tasks.json](aider-tasks.json) |  |
| [aider_probe.py](aider_probe.py) | Recording pass-through proxy in front of the production llama-server, so an Aider session's real first-turn latency and token counts can be measured. |
| [aider_task_runner.py](aider_task_runner.py) | Run real coding tasks through Aider against the production llama-server in clean disposable git worktrees, and record what actually happened. |
| [ami_bench.py](ami_bench.py) | Score the primary diarisation config against AMI - real human ground truth, standard DER. |
| [analyse_e32.py](analyse_e32.py) | Summarise the E32 concurrency sweep JSONs into a comparison table. |
| [analyse_thinking_matrix.py](analyse_thinking_matrix.py) | Resolve the E42 thinking-level matrix against the decision rule declared before the run. |
| [banking_audit.sh](banking_audit.sh) | Verify the repo is fully banked to forge - no unpushed commits, no unbanked results/docs - before/after risky legs. |
| [batch_fastpath.py](batch_fastpath.py) | Run the FAST diarisation path over a directory of real recordings; write attributed transcripts. |
| [bisect_hang.py](bisect_hang.py) | Find WHICH variable makes a model stall, by walking a ladder of conditions inside ONE model load. |
| [build_claims_json.py](build_claims_json.py) | The canonical claims registry (CLAIMS, META, CHARTS) that build_data_package.py turns into claims.yml. It can still emit the pre-r4.0 local-ai-claims.json to an explicit path, for reference only. |
| [ch1_sandbox_guard.py](ch1_sandbox_guard.py) | Confine an autonomous coding agent to its sandbox, and record every destructive attempt as a MEASUREMENT. |
| [ch1_tasks.py](ch1_tasks.py) | The C-H1 coding suite - real sparkbench commits as tasks, with the ORIGINAL tests held out as ground truth. |
| [climb_envelope.py](climb_envelope.py) | Execute the envelope rung climb with server management |
| [coding_harness.py](coding_harness.py) | Coding-model screening harness (minimal OpenAI-compatible agent loop) |
| [compare_heldout.py](compare_heldout.py) | Join E57's two crossover runs into the shallow-versus-deep table that neither run can report on its own. |
| [cost_model.py](cost_model.py) | Generate every cost figure in the report from formulas + canonical inputs (C-01/02/03). |
| [date_calc.py](date_calc.py) | the deterministic date arithmetic the H6 arm hands to a model, so the model does law and the tool does counting. |
| [decode_persona.py](decode_persona.py) | Decode nibble-packed personas from the MatrAIx Persona 1M release into readable attribute maps, and print them for inspection. |
| [diarise.py](diarise.py) | Attributed-transcript pipeline - large-v3-turbo for text + WeSpeaker for identity. |
| [diarise_eval.py](diarise_eval.py) | Score our diarisation against a reference (Otter.ai) - DER + speaker-count methods. |
| [diff_run_answers.py](diff_run_answers.py) | Compare two runs of the SAME conversation under two serving configs, on the answer STRINGS rather than on the score. |
| [e103_p0_control.py](e103_p0_control.py) | E103's P0 control - prove reasoning_effort is INERT on ThinkingCap, not partially honoured. |
| [e109_harness_knowledge.py](e109_harness_knowledge.py) | E109 arm B - ask the L5 questions THROUGH a harness, documents on disk. |
| [e112_rerun_harness_timeouts.sh](e112_rerun_harness_timeouts.sh) | E112 - re-run E109 arm B's three non-returning items on a quiet GPU with a longer cap. |
| [e114_full_harness_rerun.sh](e114_full_harness_rerun.sh) | E114 - re-run E109 arm B's three non-returning items on a quiet GPU with a longer cap. |
| [e115_effort_override_probe.py](e115_effort_override_probe.py) | E115 - does a PER-REQUEST reasoning_effort still override llama-server's --reasoning-effort flag? |
| [e116_short_turn_effort_cost.py](e116_short_turn_effort_cost.py) | E116 - what does reasoning effort COST on short, chat-shaped turns? |
| [e138_speed.py](e138_speed.py) | E138 block 1 - serve one arm, time real CODE and CHAT prompts, record draft acceptance and peak memory. |
| [e139_prompts.py](e139_prompts.py) | Build E139's fixed prompt set - real text cut to exact token counts by the model's own tokenizer. |
| [e139_speed.py](e139_speed.py) | E139 blocks 1-2 - serve one arm (halogen container or llama-server), time the fixed prompt set, record memory and power. |
| [e140_cascade.py](e140_cascade.py) | E140 runner - L3-hard through the live gateway as five arms: 27B alone, workhorse alone, and three draft-then-27B-review arms. |
| [e141_gate.py](e141_gate.py) | E141 runner - escalation gates and a workhorse effort router in front of the 27B, on L3-hard through the live gateway. |
| [e142_gate.py](e142_gate.py) | E142 runner - 27B `off` as first stage of an escalate-or-ship gate (logprob and self-check) on L3-hard through the live gateway. |
| [e146_harness_config.py](e146_harness_config.py) | Write one E146 arm's MLCommons edge-agentic config from the reference config, changing ONLY the fields Amendment 1 declares. |
| [e146_speed.py](e146_speed.py) | E146 block 1 client - time decode, prefill, decode-at-depth and determinism on ANY OpenAI-compatible server, identically for every engine. |
| [e148_dflash_accept.py](e148_dflash_accept.py) | Summarise Atlas's DFlash acceptance from an arm's server log - overall and by 4K context bucket. |
| [e152_prompts.py](e152_prompts.py) | Build E152's fixed prompt set - E139's exact-token windows plus a 100K-context prompt and six coding-agent turns. |
| [e153_prompts.py](e153_prompts.py) | Build E153's fixed prompt set - E152's exact-token windows and agent turns plus short code, prose and JSON prompts. |
| [e153_speed.py](e153_speed.py) | E153 - time one already-running OpenAI-compatible engine on the fixed Flash-Next prompt set, on the client's clock. |
| [finetune_smoke.py](finetune_smoke.py) | DEFINITIVE proof that gfx1151 (Ryzen AI Max+ 395) can TRAIN, not just infer - the check that settles whether F35/Q6's "no ROCm training stack" wall is real. Runs the full training loop (forward -> loss -> backward -> optimizer step) with a PEFT LoRA adapter on the GPU, using a TINY model built from config (no download, no memory-edge risk). If loss goes down over a few steps, on-box training works. |
| [fix_router_runpath.sh](fix_router_runpath.sh) | Repair the absolute RUNPATH in sparkrouter's llama-server build, then prove it by restarting. |
| [gen_ctx_probe.py](gen_ctx_probe.py) | Generate deterministic long-context envelope-rung probes with needle re-planting |
| [gguf_ctx_probe.py](gguf_ctx_probe.py) | Read architecture and n_ctx_train from GGUF headers without loading the model. |
| [grade_heldout_subagent.py](grade_heldout_subagent.py) | grade subagent-transport held-out depth arms with the repo's OWN multiturn grader. |
| [harness_probe.py](harness_probe.py) | E108's recording proxy - capture what an agentic harness actually SENDS, without a GPU. |
| [hybrid_bench.py](hybrid_bench.py) | Hybrid diarisation - pyannote/segmentation-3.0 as VAD, our WeSpeaker embeddings+clustering. |
| [judge_writing_pairwise.py](judge_writing_pairwise.py) | Blind pairwise judging of writing-eval drafts from two or more arms by a frontier model that is not a contestant. |
| [latency_matrix.py](latency_matrix.py) | Single-user time-to-answer for each candidate resident model, at the three prompt sizes the relay's own traffic shows. |
| [librispeech_wer.py](librispeech_wer.py) | TRUE WER against human ground truth - validates or refutes E42's Otter-based figure. |
| [mmlu_eval.py](mmlu_eval.py) | Deadlock-safe MMLU (multiple-choice world-knowledge) eval at scale. |
| [moa_test.py](moa_test.py) | Mixture-of-Agents on the local model stable - do N diverse local proposers, aggregated by a faithful local model, beat the best single local model on real drafting? Training-free, exploits our diverse-model asset. Same 10 tasks + frontier judge as every other quality run, so it slots into the comparison. |
| [mtp_acceptance.py](mtp_acceptance.py) | Extract ACTUAL speculative-decoding draft behaviour from a llama-server log, rather than trusting the flag that was requested. |
| [prefill_curve.py](prefill_curve.py) | Compare llama-server prefill throughput between runs at MATCHED depth. |
| [pyannote_bench.py](pyannote_bench.py) | Score pyannote 3.1 on the SAME AMI harness as our stack - the honest head-to-head. |
| [real_quality_run.py](real_quality_run.py) | Weekend "is it actually any good?" run - real professional use cases, quality-judged. |
| [realaudio_bench.py](realaudio_bench.py) | ours vs hybrid vs pyannote on the REAL Otter-referenced online calls - the deployment test. |
| [regrade_multiturn.py](regrade_multiturn.py) | Re-grade a finished multi-turn run from its STORED answers, so a grader repair costs no GPU and no new model output. |
| [regrade_reasoning.py](regrade_reasoning.py) | Extract content from reasoning-model outputs and re-grade dual views (as-emitted vs content-extracted) |
| [relay_bench_window.sh](relay_bench_window.sh) | Open a maintenance window on sparkrouter, run the Qwen3.8 bench legs, close it again. |
| [relay_traffic_mix.py](relay_traffic_mix.py) | Read-only summary of sparkrouter's request log, to answer which model should be RESIDENT rather than which is better. |
| [render_docx.py](render_docx.py) | Render the documents a model produced via tool use into Word-styled PNG screenshots (visual proof). |
| [require_prereg.sh](require_prereg.sh) | Refuse to run a bench stage whose pre-registration does not exist yet. |
| [run_ch1.py](run_ch1.py) | Run one C-H1 coding arm over the real-commit task suite and record the WHOLE agentic task, not a pass/fail. |
| [run_closed_record.sh](run_closed_record.sh) | Run the closed-record matters against each local model via a managed llama-server lifecycle. |
| [run_coding_eval.py](run_coding_eval.py) | Execute the coding-eval task set against a served model and score by running the code. |
| [run_deep_eval.sh](run_deep_eval.sh) | Run deep-eval promptfoo suites against local llama-server or cloud providers. |
| [run_e139_window.sh](run_e139_window.sh) | Run every E139 arm in one unattended GPU window, in pre-registered order. |
| [run_e143_window.sh](run_e143_window.sh) | Run every E143 arm (chat-recommended coding models through Aider) in one gateway window, in pre-registered order. |
| [run_e145_window.sh](run_e145_window.sh) | Run every E145 arm (the widget's option models through Aider) in one gateway window, in pre-registered order (H, E, F, G). |
| [run_e154_arms.sh](run_e154_arms.sh) | Run E154 arms over the 15-task bank - Sonnet via OpenRouter under the $25 ledger, local engines in an idle window. |
| [run_eval_pilot.sh](run_eval_pilot.sh) | Run the eval-pilot promptfoo suite against each model via a managed llama-server lifecycle. |
| [run_finetune_eval.sh](run_finetune_eval.sh) | Phase 3 - eval the house-style fine-tuned Mistral-24B on the held-out 10 tasks vs the SAME base at the SAME quant (Q8, so only the LoRA differs, not quant), frontier-judged. The F37 verdict: does the on-box fine-tune move usability off ~3.0? |
| [run_h6_date_arm.py](run_h6_date_arm.py) | the H6 arm - run a graded question set with and without a deterministic date tool, and account for BOTH directions. |
| [run_kw_all.sh](run_kw_all.sh) | Run E74 (KA-H1) across three local arms and two packs, unattended, after the coding pilot releases the GPU. |
| [run_kw_eval.py](run_kw_eval.py) | Run one arm over the KA-H1 real-document knowledge-work bank. Records everything, scores nothing. |
| [run_longctx_eval.py](run_longctx_eval.py) | E35 - needle-at-depth retrieval quality at 8K/32K/64K/128K, tokenizer-measured, local or cloud. |
| [run_multiturn_eval.py](run_multiturn_eval.py) | Run the multi-turn conversation against a served model, keeping full history, graded without a judge. |
| [run_ps_eval.py](run_ps_eval.py) | Run the professional-services knowledge-work eval against a served or cloud model, graded objectively. |
| [run_ps_eval_subagent.py](run_ps_eval_subagent.py) | run a ps-eval tier through Claude Code subagents instead of HTTP, and grade it with the repo's own grader. |
| [run_step8_leg.sh](run_step8_leg.sh) | Run one Step 8 llama-bench leg with amdgpu thermal capture before/after. |
| [run_writing_eval.py](run_writing_eval.py) | Run the technical-writing eval against a served or cloud model, graded without an LLM judge. |
| [score_aabr.py](score_aabr.py) | score banked AABR transcripts mechanically, keeping the evidence classes segregated. |
| [score_abstain.py](score_abstain.py) | Score E76 abstention runs mechanically - unsupported assertions, correct abstentions, and the price paid on answerable controls. |
| [score_capped_atlas_arm.py](score_capped_atlas_arm.py) | Server-side scoring for any Atlas DFlash arm (E150 M5, E151 M6, later ones) against M3p and M1p on the same first N turns, with acceptance split by first turn against later turns. |
| [score_e101.py](score_e101.py) | Score E101's five cells against its six pre-registered predictions. |
| [score_e107.py](score_e107.py) | Score E107's temperature sweep against its six pre-registered predictions. |
| [score_e138_blocks.py](score_e138_blocks.py) | Score E138 blocks 2-4 (quality banks, Aider, pi on Bonsai 2 PQ2_0) against results/e138-prereg.md P7-P10 and amendments 3-4. |
| [score_e146.py](score_e146.py) | Score E146 (Atlas vs llama.cpp on Strix Halo) against results/e146-prereg.md and Amendment 1. |
| [score_e149.py](score_e149.py) | Score E149's arm M4 against its pre-registered predictions, server-side when the harness was capped. |
| [score_e154.py](score_e154.py) | Score E154 arms from results/e154/raw/<arm>/<task>.json against the pre-registered fields and P1-P7. |
| [score_e159.py](score_e159.py) | Score E159 arms against the prereg's fields (pass_count, tokens_median, wall_median_s) and P1-P6. |
| [score_e160.py](score_e160.py) | Score E160 (KFL vs KX) against the prereg's fields and predictions P1-P11. |
| [score_e77.py](score_e77.py) | Score E77 - the correct-to-wrong rate between an f16 KV baseline and each quantised arm, plus byte identity of the answers. |
| [score_e77_timings.py](score_e77_timings.py) | Extract prefill and decode rates per KV precision from E77's quiet-GPU re-run server logs. |
| [score_e79.py](score_e79.py) | Score E79 by BAND and by direction - what the tool converted, what it destroyed, and which of those was infrastructure. |
| [score_e84.py](score_e84.py) | Score E84's KA-H2 ladder - the same questions asked at three context sizes, plus the KV-allocation isolator. |
| [score_e87.py](score_e87.py) | Score E87 - decode/prefill throughput, f16 vs f16+fa vs q8_0 KV, on relay build 9865. |
| [score_kw_eval.py](score_kw_eval.py) | Score banked KA-H1 transcripts mechanically. Never calls a model. |
| [score_l5_bands.py](score_l5_bands.py) | Score L5 runs by BAND, because the tier's total is the least informative number it produces. |
| [serve_bench.py](serve_bench.py) | llama-server lifecycle + concurrency load harness (Step 9; Phase B server-lifecycle core). |
| [session_bench.sh](session_bench.sh) | Hold ONE maintenance window for a whole bench session and run arms back to back inside it. |
| [silence_bench.py](silence_bench.py) | Measure when whisper INVENTS speech out of silence. Pre-reg: e41-...-prereg.md. |
| [smoke_first_token.py](smoke_first_token.py) | Does this model emit a FIRST TOKEN at all? Separates a stalled decode from a runaway generation, cheaply. |
| [soak_load.py](soak_load.py) | Repeated controlled load+first-decode cycles on one model, to measure a FAULT RATE rather than diagnose a cause. |
| [sparkrouter_discovery.py](sparkrouter_discovery.py) | Read the live serving identity of the production llama-server, so a client is configured from what is actually running rather than from notes that have drifted. |
| [spk_embed.py](spk_embed.py) | Speaker-embedding extractor (WeSpeaker ResNet34-LM ONNX) + cosine similarity helper. |
| [spk_embed_validate.py](spk_embed_validate.py) | Positive control - prove the speaker embedder discriminates speakers before trusting it. |
| [strip_task_transcripts.py](strip_task_transcripts.py) | Split coding-harness task files into a committable scoring record and a full copy kept on disk. |
| [target_speaker.py](target_speaker.py) | "Is it Alastair or not?" - target-speaker detection, sidestepping the auto-k problem. |
| [tool_router.py](tool_router.py) | Decide, per question, whether to offer the date tool at all - the classifier E79 said the tools branch needs before it can pay. |
| [tooluse_harness.py](tooluse_harness.py) | Benchmark local models on office tool use (OpenAI function calling) - can a model correctly call create_word_document to produce a real .docx, select among tools, and chain steps? |
| [tooluse_harness_v2.py](tooluse_harness_v2.py) | Extensive tool-use benchmark (E33) - reliability (N runs), 6 tools, 7 task categories, 4 models. |
| [upgrade_router_llama_binary.sh](upgrade_router_llama_binary.sh) | Swap sparkrouter's llama-server build to the newer one, with acceptance test and rollback. |
| [vad.py](vad.py) | A REAL voice-activity detector (Silero ONNX) for the speaker pass. |
| [validate_conversation_heldout.py](validate_conversation_heldout.py) | Assert E57's crossover holds - one ask per question, an identical middle across both orders, and a filler disjoint from the held-out key. |
| [validate_conversation_long.py](validate_conversation_long.py) | Prove E56's paired anchors are byte-identical, its filler cannot corrupt the answer key, and every failure shape is reachable. |
| [validate_expert_tasks.py](validate_expert_tasks.py) | Prove every expert coding task is both SOLVABLE and DISCRIMINATING before it scores any model. |
| [validate_expert_tasks_v2.py](validate_expert_tasks_v2.py) | Prove every v2 expert task is SOLVABLE and DISCRIMINATING before it scores any model. |
| [validate_expert_tasks_v3.py](validate_expert_tasks_v3.py) | Prove every v3 expert task is SOLVABLE, and discriminating against BOTH a naive and a competent-but-wrong solution. |
| [validate_multiturn.py](validate_multiturn.py) | Prove the multi-turn grader separates, every conversation failure shape is reachable, and the script's ORDER is sound. |
| [validate_ps_eval.py](validate_ps_eval.py) | Prove the PS-eval graders score a perfect answer set correctly AND catch each named failure mode. |
| [validate_ps_eval_l2.py](validate_ps_eval_l2.py) | Prove the L2 graders score a perfect answer set correctly AND catch each named L2 failure mode. |
| [validate_ps_eval_l3.py](validate_ps_eval_l3.py) | Prove the L3 tier changes ONLY the pack size, and that wrong-document retrieval is detectable. |
| [validate_ps_eval_l4.py](validate_ps_eval_l4.py) | Prove the L4 graders separate, every named trap is reachable, and no key collides with a figure in the pack. |
| [validate_ps_eval_l5.py](validate_ps_eval_l5.py) | The L5 gate - prove the bank before any model sees it, with synthetic respondents whose signatures the graders must reproduce. |
| [validate_ps_eval_pr1.py](validate_ps_eval_pr1.py) | Prove the PR1 bank is balanced, its grader separates FLAG from PROCEED in both directions, and its prompt actually builds. |
| [validate_tooluse_conditional.py](validate_tooluse_conditional.py) | Validate the conditional tool-use graders against synthetic respondents before any model is scored. |
| [verify_cloud_results.py](verify_cloud_results.py) | Generate the canonical cloud-eval results table (counts + Wilson CIs) directly from the raw promptfoo JSONs, and verify hand-maintained summaries against it. |
| [wer_bench.py](wer_bench.py) | Measure transcription DISAGREEMENT vs an Otter.ai reference, across models/configs. |
| [wilson_ci.py](wilson_ci.py) | Calculate Wilson score confidence intervals for proportions (95%, two-tailed) |

**Folders:** [coder-bakeoff/](coder-bakeoff/) · [e88/](e88/) · [e90/](e90/) · [e91/](e91/) · [e92/](e92/) · [e93/](e93/) · [e97/](e97/) · [gateway/](gateway/)
