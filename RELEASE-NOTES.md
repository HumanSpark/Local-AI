# Release Notes - sparkbench-data-r6.3

Data package for the Local AI resource. sparkbench ships evidence, findings, and the claims registry;
reader-facing prose is the owner's and webby renders it (sparkbench docs/REPORT-STANDARD.md).

## This release (r6.3)

- **Findings:** 204 in FINDINGS.md, newest F204.
- **Claims:** 64 in claims.yml (26 current, 18 historical, 17 qualified, 3 superseded).
- **One plain sentence for every claim** (`claims.json`, `statement_plain`): all 64 claims, written for a business
  reader, with sample size and limits kept.
- **The cost chart says what each bar covers** (`includes` on each bar).
- **Memory limits restated** (C-CAPACITY-TIERING-001): on a clean, freshly restarted box, models using up to about
  113 GB of memory have loaded and run ([F109](FINDINGS.md#f109)). The July freezes needed a trigger: heavy disk
  activity beside the load, or a retry after a crash ([F24](FINDINGS.md#f24), [F28](FINDINGS.md#f28),
  [F193](FINDINGS.md#f193)). Size alone did not cause them.
- **HTR's maker on v0.2.5:** single-user speed is about the same, as measured here; he reports gains with several users
  at once ([E179](results/e179-results.md)). Not yet measured here.
- **Plainer engine wording** (`setups.json`): HTR is now "HTR backup engine"; side notes about name disputes and makers'
  own figures are gone from the engine cards; optional fields with nothing on record are omitted rather than saying
  "not recorded here"; setup roles use plain words.


## Earlier releases

### r6.2

- **Energy per answer, against a fridge-freezer** ([results/energy-per-answer.md](results/energy-per-answer.md)): the
  box draws about 120 W at the wall while working and about 7 W idle (measured on a Tapo smart plug; the plug's export
  and app screenshots are in results/energy/). An everyday coding fix uses about 20 Wh, what a fridge-freezer uses in
  27 minutes, or under a cent of electricity on the actual tariff.
- **Ling-3.2-air, final:** 1 of 15 everyday fixes and 0 of 10 large changes; switching its thinking off made it loop
  ([F203](FINDINGS.md#f203)).
- **The newer HTR release (v0.2.5):** no measurable speed change at one user, and 3 of 3 large changes still solved
  ([E179](results/e179-results.md)); it stays the backup engine.
- **Engine cards** for each engine: who makes it, what sets it apart, licence, versions tested, test dates and a project
  link, in `setups.json` (`meta.engines`). Each claim's review date is now never earlier than its test date.


### r6.1

- **Rewritten to lead with what works and what to do.** The README opens with what the box does well, where it
  falls short and what I'd do, in place of a dated list of recent results (those stay in this file). The five kinds
  of work are ordered by how much a firm leans on them, each with a plain answer. Capabilities follow the same
  business order, with coding last. The frontier page opens the same way.


### r6.0

- **New page: [how it compares with frontier models](FRONTIER.md).** Quality and speed are kept apart. The box is
  level with Anthropic's models on everyday and medium coding fixes, much slower, and clearly behind on large changes
  and on client drafting. It does not claim to beat the labs' hardware.
- **Claude on the ten large changes ([E178](results/e178-results.md), [F204](FINDINGS.md#f204)).** Claude Sonnet 5.5,
  Opus 5.5 and Fable 5.2 each solved all ten (median 3.3, 6.8 and 7.1 min a change); production solves five.
- **Three frontier claims** (`C-FRONTIER-EVERYDAY-FIXES-001`, `C-FRONTIER-LARGE-CHANGES-001`, `C-FRONTIER-DRAFTING-001`).
- **Plain-language fields** for the website: `setups[].reason_plain`, `setups[].setting_plain`, `engines[].why_plain`
  and `meta.capability_frontier` in `setups.json`; `claims[].experiments` in `claims.json`. All additive; nothing renamed.
- Each capability page now opens with one line on how it compares with the frontier.


### r5.19

- **What works best, by capability.** New pages under [capabilities/](capabilities/README.md): for each kind of
  job (text and reasoning, coding agents, office tools, vision, speech to text, who said what, voice output, images,
  music, memory, fine-tuning) the setup in production, the best alternative and why, what else was tried, and the
  experiments behind it, best results first. Vision says plainly that it has not been tested yet.
- **Engines compared separately** ([capabilities/engines.md](capabilities/engines.md)): Halogen in production, HTR on
  vLLM as the fallback, every other engine with where it stands, and only same-model comparisons as evidence, each
  with its workload and conditions.
- **New: `setups.json` and `experiments.json`** beside `claims.json`. Every setup is a model, an engine and a setting
  with a plain role name, a status and a one-line reason; every experiment from E135 on (and the July ones the pages
  cite) carries its track, capabilities, engines, kind of test and result. The build fails on an untagged experiment
  or an unknown label.

#### Changed claims (old -> new)

- (none.)

#### Retracted claims

- (none.)

### r5.18

- **A new README** for IT readers: what production runs now, what changed recently, the five research tracks, how
  to check one number yourself in five minutes (tag r5.18), and what a reader can and cannot check.
- **Five track pages** under [tracks/](tracks/): each track's question, why the test fits it, the current answer, and
  every claim on that track with its status, dates and exact evidence. The coding chart is on the Unattended work page;
  the five-engine speed table and the two speed measurements of production, with what differs between them, are on
  the Running it page.
- **New finding F203** (E176): Ling-3.2-air writes about 37% faster than production's model on llama.cpp but solved
  0 of 10 hard coding changes, against production's 5. Its runs on the two easier coding banks are under way.
- July experiments whose numbers an August experiment also uses are now written with an A (E32A, E35A to E50A);
  [GLOSSARY.md](GLOSSARY.md#experiment-numbers-used-twice) says which is which.
- `tools/score_e162.py` now writes byte-identical `results/e162/score.json` on every run (one field's key order
  varied between runs); the README's five-minute check uses tag r5.18.
- New evidence: `results/e176-results.md`, `results/e176/`.

#### Changed claims (old -> new)

- (none.)

#### Retracted claims

- (none.)

### r5.17

- **Every claim now says when it was tested, whether it still holds, and where its exact evidence is.** Each of the
  61 claims carries `tested`, `reviewed`, `status`, `track`, a plain and a technical name for the setup, its exact
  `record` (file and anchor, replacing whole-index sources) with a `source_url` pinned to this release, and an
  `access` level (inspect, recalculate, rerun or private, with the reason). Status after the 2026-11-24 review: 23
  current, 17 qualified, 18 historical, 3 superseded. Meanings: [GLOSSARY.md](GLOSSARY.md#claim-status).
- **New: `claims.json`**, the same rows as `claims.yml` for machines; the website renders it.
- **Unique experiment IDs.** Three July series reused numbers that different August experiments also use: the July
  tool-use tests are now TU32 and TU33, the July router and multi-user tests RT35 to RT37, and the July
  meetings and transcription series MT38 to MT50. File names are
  unchanged and each record says what it was published as. [GLOSSARY.md](GLOSSARY.md#experiment-numbers-used-twice).
- **`tools/cost_model.py` recalculates from a clean checkout** (it read a fixed path on our machine); output unchanged.
- **Full release history** below, from r4.0.
- **New findings.** [F198](FINDINGS.md#f198): starting a GPU engine a second after another exits can crash the
  kernel, so we wait for GPU memory to settle first. [F199](FINDINGS.md#f199): an 8-bit conversation memory never
  helps production's model on llama.cpp. [F200](FINDINGS.md#f200): a paired tool-result question catches a silently
  broken chat template. [F201](FINDINGS.md#f201): three local song models run here; none matched the owner's taste in
  style. [F202](FINDINGS.md#f202): production's model compressed with the community HTR method keeps its coding
  quality (6/10 against production's 5/10 on ten hard fixes) but runs slower than Halogen.
- New evidence: `results/e173-results.md`, `results/e174-results.md`, `results/e175-results.md`,
  `results/e177-results.md` and their folders.

#### Changed claims (old -> new)

- C-TOOLUSE-CONDITIONAL-001 rewritten: "Mistral was the exception" was overturned by the 13-task expansion (F73). Now:
  every model tested also flags the case where the condition is false; Mistral was the worst on 13 tasks.
- Superseded (production on Halogen reads long prompts several times faster): C-LONGCTX-USABLE and
  C-LONGCTX-FIRST-ANSWER, by the new C-LONGCTX-FIRST-ANSWER-PROD (first word after about 5.5 s at 8K and 22.4 s at
  32K, F202). C-REASONING-TOKEN-TAX-LOCAL, by F186 and F187: production has been a reasoning model at effort low
  since 13 November.
- Every other claim keeps its number and text; its status says whether it still supports today's advice.

#### Retracted claims

- (none.)

### r5.16

- **Clearer names; no finding, claim, number or piece of evidence changed.** Findings are the same 197 (newest F197)
  and claims the same 60 as r5.15.
- Where a page named a test setup only by a letter code from another experiment ("E43 arm B", "E89 arm A", "F 0.997,
  I 1.000, H 0.987"), it now uses a short name ("E43's `xhigh` run", "E89's prefill-parallelism test", "production
  0.997, Inkling 1.000, Hy-Memory 0.987"). Experiment pages that refer to other experiments' arms open with one line
  saying what those arms were.
- Engines named in FINDINGS.md (Halogen, Atlas, Talus, Strata, Loom, Engram) get a one-line plain description where
  they first appear.
- Changed files: FINDINGS.md; experiments/E44-E49, E51, E52, E76, E80, E81, E112-E114, E119; docs/HARNESS-RULES.md;
  reports/2026-11-evidence-entries-coding.md; results/e136-results.md, e142-results.md, e171-results.md.

#### Changed claims (old -> new)

- (none. Production and its setting are unchanged.)

#### Retracted claims

- (none.)

### r5.15

- **New finding F196 (E170): on memory-keeping jobs, production, Inkling-2-Mini and Tencent's Hy-Memory are all
  near-perfect.** Fifty invented memory jobs full of traps. Inkling made no mistakes, production one, Hy-Memory a few
  (it kept suggestions the person had turned down). Inkling was 6.5 times slower and gave no answer on 5 of 20
  updates, so production runs the nightly memory job. Caveat: that slowdown was our conversion on plain llama.cpp with
  no drafter, plus an undefined key in our own test, not the model alone; a fuller Inkling test is planned.
- **New finding F197 (E171): Tencent's Hy4-Flash (220B) runs stably on this machine but slowly, and an hour per task
  is too short for it.** Packed by the community Strata engine, it loaded in 38 seconds and ran all day without
  trouble. It wrote about 24 tokens a second, a third of its packager's figure. On the ten big coding changes it
  passed 3 to production's 5, and every task used its full hour. The two passed different tasks; production's
  passes all took more steps than Hy4 managed in an hour. Too slow for this budget, not shown to be less capable.
- New evidence: `results/e170-results.md`, `results/e170/`, `results/e171-results.md`, `results/e171/`. E171's
  per-task records are withheld (WITHHELD.md): they quote private repositories.

#### Changed claims (old -> new)

- (none. Production and its setting are unchanged.)

#### Retracted claims

- (none.)

### r5.14

- **README: what production runs now covers speech too.** The section gains a table of all three production jobs:
  the language model (unchanged), speech to text (Whisper large-v3-turbo with voice-activity detection and
  host-versus-other tagging, since 18 July 2026, F44-F46) and text to speech (Chatterbox cloning VCTK speaker p239,
  since 1 August 2026, F56; Kokoro bf_emma as the opt-in fallback).
- **New page VOICES.md with eleven audio samples** in `voices/`: the two VCTK reference recordings, the production voice
  (a short take and the 68-second sample that closed the narrator search), the runner-up voice, VoxCPM2's clones of
  both voices, Kokoro bf_emma, and one garbled CosyVoice3 render (F55). Most read the same line. F5-TTS and Fish
  s2-pro samples are not published (licence). The VCTK CC BY 4.0 attribution is on the page.
- **VOICES.md documents how numbers, dates and symbols are written out before speaking**, with a before/after pair
  in the production voice (samples 10 and 11): Chatterbox does no number handling, and the Whisper intelligibility
  check cannot see a misread number. Ships the rewriter `tts-bench/speakable.py` and its 183 tests,
  `tests/test_speakable.py`.
- No finding, claim or evidence file changes.

#### Changed claims (old -> new)

- (none.)

#### Retracted claims

- (none.)

### r5.13

- **New finding F194 (E167): on big multi-file changes the best local setup passes half of what a frontier model does.**
  Ten real changes of 150-2,400 lines across 3-9 files, each with the project's own tests in full view. GPT-6.1 Sol
  passed 10 of 10, at about two minutes a task and $1.95 in all. Production (Flash-Next on Halogen) passed 5, at about
  eleven minutes a task; Ornith 35B passed 3. The local models stopped and declared the work done while tests still
  failed, so more time would not have helped.
- **New finding F195 (E168): hide the tests and both local setups fall to 1 of 10.** Same ten changes, with only the
  developer's own note and a list of the names the change adds. Production fell from 5 to 1, Ornith from 3 to 1. Most
  of the local models' skill on big changes is building to a specification they are shown. The cloud model could not be
  scored on this version (its budget ran out after five tasks on an earlier version), so this does not say how far
  local trails the frontier with the tests hidden.
- **New finding F193: the graphics-memory deadlock is back on kernel 7.0.0-42.** A 75 GiB model load froze the GPU
  after an earlier load had crashed it the same day, and only a power cycle cleared it. F109's "newer kernels fixed
  it" now holds only for loads on a freshly rebooted machine.
- New evidence: `results/e167-results.md`, `results/e168-results.md`, `results/e166/`. The E167/E168 task banks and
  per-task records are withheld (WITHHELD.md): they quote private repositories.

#### Changed claims (old -> new)

- Coding recommendation: "the best local setups match Sonnet 5.5 and Opus 5.5 on real repository work" (F183) ->
  holds for small issue-style fixes; large multi-file changes are frontier work (F194, F195).
- F109 (deadlock not reproduced on kernel 7.0): -> holds for clean-state loads only (F193).

#### Retracted claims

- None.

### r5.12

- **New finding F191 (E164): Qwen4 Max, the first Qwen4 model, tested through the cloud.** It is not available
  to run locally. On ten client-drafting jobs a blind judge put it slightly ahead of production (4 wins to 2), level with
  Claude Sonnet 5.5 (4 to 5) and clearly behind GPT-6.1 Sol (1 to 7). It invented no figures. It is the yardstick for
  open Qwen4 models when they ship. Total cost $4.08.
- **New finding F192 (E165): our everyday test suites were marking models down for following their own instructions.**
  The tool-use test asked for letters to seven clients missing from its pretend database while telling the model to
  look clients up and to ask when information is missing; models that asked were failed. The conversation test told the
  model that anything contradicting the record loses to the record, then marked it wrong for not applying a "correction
  for the file". An answer key was wrong, and three graders marked correct answers wrong. Every model lost marks,
  production included. Corrected, all five tested setups pass 36 of 36 tool tasks, and every one applies a correction
  without accepting the false claims the test also plants. Each fix carries a regression check shown to fail on the old
  code. Original and corrected scores are published side by side in `results/e165-results.md`.
- New evidence: `results/e164/`, `results/e165/`, `results/e164-results.md`, `results/e165-results.md` and their
  pre-registrations.

#### Changed claims (old -> new)

- F190 (Loom): "passed 28 of 36 tool tasks against Halogen's 33" -> both pass 36 of 36 on the corrected test.
- F186/F187 (production setting): unchanged; the corrected scores leave the comparison within noise.
- Suite scores published in r5.6-r5.11 for tool use, the two conversation tests, L5, writing and kw-eval understate
  every model; read them beside E165's corrected columns.

#### Retracted claims

- F190's tool-use clause (r5.10, reworded in r5.11): Loom has no tool-use shortfall. It was the test.

### r5.11

- **F190 corrected: Loom's lower tool-use score is a behaviour difference, not a fault.** r5.10 said that on
  conditional tool tasks Loom "looked the client up and then stopped". That is what it did, but transcripts from an
  unscored re-run of the five tasks (3 runs each, Loom and Halogen) show why. The client lookup in those tasks returns
  "no client record found", and Loom asks the user for the details. In the reminder task it asks for today's date
  rather than guess one. The test's own instructions say to ask when information is missing, while its grader only
  counts the task done when the document or reminder is created. Halogen pressed on in the same situations. The
  scores (28 against 33 of 36) and every other F190 figure are unchanged.
- New evidence: `results/e163/raw/transcripts/LM.jsonl` and `HS.jsonl`, and the re-run's result files.

#### Changed claims (old -> new)

- (none; F190's wording is corrected in FINDINGS.md.)

#### Retracted claims

- (none.)

### r5.10

- **New finding F190 (E163): AMD's agent-ported HRX Loom engine beats llama.cpp, but not production Halogen.**
  AMD announced on 2026-11-13 that coding agents ported 51 models, including our production Flash-Next, to its new
  Loom engine in four days. We ran Loom (dev build 0.2.0.dev0), upstream llama.cpp `9fba51d` on the same GGUF, and
  production's Halogen engine, all timed by one client.
  - Against llama.cpp the claim holds: 2.69x on 32K-token prefill (979 against 364 tok/s), 1.49x on decode.
  - Against Halogen it does not: about level on 32K prefill (979 against 879, Halogen's runs spread 791 to 1,239),
    0.61x at 8K and 0.72x on decode.
  - On the E160 suites at effort low, Loom matched Halogen on document Q&A, refuse/comply, kw-eval and conversation,
    and fell behind on writing (4 against 6 of 7, derived figures) and tool use (28 against 33 of 36). On conditional
    tool tasks it looked the client up and then stopped.
  - The prereg rule: production stays on Halogen.
- **Two transport amendments are disclosed.** Loom rejects requests with no or an unknown `model` and serves
  `/healthz` rather than `/health`, so the suites reached it through a small proxy that fixed only those. One suite
  (L5) sent no item before the second fix and was re-run whole.
- New evidence: `results/e163-prereg.md`, `results/e163-results.md`, `results/e163/score.json`, the three arms'
  `speed.json` files and the suite results.

#### Changed claims (old -> new)

- (none.)

#### Retracted claims

- (none.)

### r5.9

- **New finding F189 (E162): on client-shaped drafting, GPT-6.1 Sol beats production Flash-Next at every effort.**
  The tasks were ten realistic jobs for invented businesses: a proposal section, meeting actions, a complaint reply, a
  contract explainer and others. Five arms drafted them: production at low, medium and xhigh, Claude Sonnet 5.5 and
  GPT-6.1 Sol. Two blind judges, grok-4.7 and kimi-k3.1-pro, compared every pair in both orders.
  - GPT won 7 to 9 more tasks than it lost against every local effort, on both judges.
  - Claude beat low on both judges. Against medium one judge gave +1, and against xhigh the judges disagreed.
  - Medium and xhigh beat low, against the prediction.
  - The judges' reasons, two of them confirmed by hand, are unsupported commitments and missing context. Invented
    figures were not the problem: all 12 raw "invented figure" flags were false positives on review (euro-thousands
    conversions, labelled calculations, and a wrong weekday in our own prompt).
  - The pre-registered rule fired: client-facing drafting is frontier work, or a local draft a person edits.
- **Amendment 1 is disclosed.** Kimi returned 51 of 200 replies empty. Each was re-asked once with only the token cap
  raised, after the tallies had printed. First-pass and after-retry completion and costs are reported separately, and
  the conclusions hold on the first pass alone.
- **Coding harness: the task budget is now a hard cap, and every started task leaves a record** (HARNESS_VERSION
  2026-11-15.1, `docs/HARNESS-RULES.md` Rule 15). This prompted no re-run. In E158, Ornith 1.5 122B's tenth task
  stays marked missing and scored as a fail.
- **README:**
  - The chart caption now says a one-task difference is within noise (F183).
  - Ornith 122B's minutes note now says its tenth task was stopped at the 70-minute limit and scored as a fail.
- New evidence: `results/e162-prereg.md`, `results/e162-results.md`, `results/e162/score.json`,
  `results/e162/adjudication.json`, `results/e162/grade.json`, the five draft files and both judges' verdict files.

#### Changed claims (old -> new)

- (none.)

#### Retracted claims

- (none.)

### r5.8

- **New finding F188 (E161): MoE "expert helpers" do not pay on this machine.** Tandem-style schemes keep the
  busiest experts in fast graphics memory and have the CPU or a second card compute the rest. On this box's single
  shared memory pool every version was slower than keeping the model wholly on the graphics side. Moving experts to the
  CPU cost 10-32% of decode speed (llama.cpp `--n-cpu-moe` 4/12/24). tandem.cpp built and ran on this GPU, but its
  automatic cache never switched on (it reads the small BIOS carve-out as the free graphics memory). A 24 GiB cache set
  by hand came out 16% slower than the same engine without it, and nearly exhausted memory.
- **Routing skew:** the busiest fifth of Flash-Next's 512 experts per layer take about 70% of routing on code, documents
  and prose alike. Code uses a different hot set from documents and prose (overlap 0.18-0.19), while documents and
  prose share theirs (0.70). Mixed precision by hotness is therefore not pursued as planned.
- New evidence: `results/e161-prereg.md` (amendments 1-2, both declared before the runs they affect),
  `results/e161-results.md`, `results/e161/speed-*.json`, `results/e161/skew.json`. The skew corpora quote private
  repositories and the imatrix files are 1.1 GB each; neither ships.

#### Changed claims (old -> new)

- (none.)

#### Retracted claims

- (none.)

### r5.7

- **README: the production setting.** A new section says what the machine serves since 13 November 2026
  (Qwen3.8-Flash-Next on Halogen, community chat template, reasoning effort low unless a request asks for more) and
  why, from F186 and F187. The coding chart's caption no longer says a lower effort "is being measured"; it points to
  F187. No finding, claim or evidence file changes.

#### Changed claims (old -> new)

- (none.)

#### Retracted claims

- (none.)

### r5.6

- **New finding F187 (E159): on coding, lower reasoning settings are within noise of the maximum.** On the same
  ten real fixes, Qwen3.8-Flash-Next scored 8/10 at maximum thinking, at medium, at the community chat template's
  default and at community template + low; stock template + low scored 7. Community template + low took 5.8 minutes
  per fix against 19.1, with about a third of the thinking (17,802 tokens against 50,114). F183's 9/10 was measured at
  the stock template's unchosen maximum; its 2026-11-12 addendum now points here.
- **New finding F186 (E160): community template + low as the production setting, tested on eight kinds of work.** Against
  maximum thinking, it scored level or better on hard document questions (23 v 23 of 24), refuse-or-comply (12 v 12),
  conversations (9 v 8, 18 v 15), tool use (33 v 33 of 36) and dates with a tool (6 v 6). Writing was within noise
  (6 v 7 on the automatic check; a blind Opus 5.5 judge gave 1 win, 4 ties, 2 losses). It fell short on answers from a
  large document pack (24 v 26): one miss is a grading artefact, the other a percentage the documents never state. The
  battery took 20.6 minutes against 49.9. Three of eleven preregistered predictions failed; the results file reads each.
- New evidence: `results/e159-results.md`, `results/e160-results.md`, `results/e159-prereg.md`, `results/e160-prereg.md`.
  The per-task records quote the owner's private repositories (E159) and internal documents (E160 answers), so the raw
  directories are withheld as for E154-E158; the results files carry every score.

#### Changed claims (old -> new)

- (none.)

#### Retracted claims

- (none.)

### r5.5

- **README: speed and the machine.** Under the coding chart, a table adds each setup's engine and median minutes
  per task (from the E156 and E158 results tables). A second table shows one model, Qwen3.8-Flash-Next, on five
  engines: decode speed, prefill at 32K tokens and time to first token, from F180 (E153). A callout box states the
  machine's specification. Every figure in both tables is checked at build time against the results line it cites.
- No finding, claim or evidence file changed.

#### Changed claims (old -> new)

- (none.)

#### Retracted claims

- (none.)

### r5.4

- **Easier to browse; no finding, claim or evidence changed.** FINDINGS.md opens with an index of every
  finding (title, kind, date, experiment and status copied from each entry, linked to it), grouped by kind, and every
  finding has a link back to the index. New claims.md renders claims.yml as a table with clickable evidence links. New
  results/README.md lists every experiment by number with its write-up, pre-registration, results and data. tools/,
  docs/, eval-suites/ and tts-bench/ each gain a README listing their files with each file's own description.
- **experiments.md split.** At 1 MB it was too large to browse; each experiment now has its own file in experiments/
  (E1 to E134), and experiments.md is the index. Every line moved, none was edited, and every existing citation of
  experiments.md still resolves.
- **Internal file headers hidden.** The "File / Purpose / Overview" lines that opened most markdown files rendered on
  GitHub as large headings; they are now inside an HTML comment. Nothing was removed.
- **Repository metadata.** LICENSE (CC BY 4.0, for the data and documents) and tools/LICENSE (MIT) so GitHub shows the
  licence the README already stated; CITATION.cff for a "Cite this repository" button; a .gitattributes so GitHub no
  longer describes the repository as a Python project.
- **One chart in the README:** real coding fixes solved out of 10, drawn at build time from the C-CODING-HARD claims
  (F183, F185), in light and dark versions.
- **INDEX.md removed.** It was stale (it listed findings to F79 and experiments to E54) and the generated indexes above
  replace it.

#### Changed claims (old -> new)

- (none.)

#### Retracted claims

- (none.)

### r5.3

- **F183 amended (addendum 2026-11-12): the condition the 9/10 was measured at.** Flash-Next on Halogen ran at
  reasoning effort `xhigh`: the harness sent none, and the model's stock chat template defaults a missing effort to `xhigh`.
  That is why it spends a median of 59,437 output tokens and 21.3 minutes per task. A lower effort per request is
  possible and is now being measured (E159, pre-registration results/e159-prereg.md, included). The 9/10 stands for `xhigh`;
  whether `medium` or `low` keep it is not yet known.
- **New provenance:** MANIFEST.md records the E155 quality-ceiling models (GLM-5.3-Flash UD-IQ2_XXS, DeepSeek-V4.1-Flash
  Coder IQ2_XXS), pinned and sha256-verified. E155 has no result yet (4 of 10 tasks run for one arm before an interruption);
  no claim depends on it.
- **Tooling:** tools/run_e154_arms.sh gains the E159 effort arms and a deadline guard; tools/relay_bench_window.sh now
  closes a bench window correctly when production serves through Halogen alone (it previously left the gateway's health
  check reporting maintenance).

#### Changed claims (old -> new)

- (none. C-CODING-DEFAULT is unchanged; its evidence is now qualified by the F183 addendum.)

#### Retracted claims

- (none.)

### r5.2

- **Local coding on harder real repository work (E156, E158; F183-F185).** On 10 real multi-file fixes from the owner's
  repositories, scored by each project's own hidden tests in a sealed container: Qwen3.8-Flash-Next on Halogen 9/10, Ornith
  1.5 35B on llama.cpp 9/10, Qwen3.8-27B on Talus, Tess 4.5 27B and Raon-1 mini 8/10, Claude Sonnet 5.5 and Opus 5.5 8/10,
  Ornith 1.5 122B 6/10, Qwen3-Coder-30B 2/10. The best local setup takes a median 21.3 minutes per task against Sonnet's
  2.5. Tess 4 35B could not be loaded by upstream llama.cpp. Ten new claims (C-CODING-HARD-*).
- **F184 (method):** hidden tests demanded details five task prompts never stated; reading the first cloud failures found
  all five, automated prompt checks found none.
- **New evidence:** results/e154-results.md, results/e156-results.md, results/e158-results.md and the E158
  pre-registration. The per-task records, the task bank (results/e154/, results/e156/, results/e158/) and the E154 and
  E156 pre-registrations are withheld from this package: they quote the owner's private repositories. They stay in the
  sparkbench repository.
- **New evidence-page source:** reports/2026-11-evidence-entries-coding.md (F183-F185, the owner's six-part structure).
- **Report roles:** docs/REPORT-STANDARD.md - sparkbench drafts reader prose marked DRAFT, the owner rewrites, webby renders.
- **Public copy cleaned (2026-11-07 audit):** internal host names, home-directory and vault paths are replaced with
  neutral names (benchhost, lanhost, /home/bench, /opt/vault), and the synthetic test documents' contact details use
  reserved .invalid domains and unallocated +353 1 000 numbers, applied identically to the documents and the model
  answers that quote them. claims.yml evidence paths now name where each file sits in this package. The repository
  history was consolidated into one commit at r5.2.

#### Changed claims (old -> new)

- **C-CODING-DEFAULT** (owner decision 2026-11-07): "Qwen3-Coder-30B is the recommended default (GLM-4.7-Flash as
  fallback)" -> "Qwen3.8-Flash-Next on Halogen is the recommended default, with Ornith 1.5 35B on llama.cpp as fallback".
  Source moved from docs/plans/2026-07-12-coding-screen-10-realproject-results.md to results/e158-results.md.

#### Retracted claims

- (none.)

### r5.1

- **Five vendor and community claims tested on the box, and five claims added for them (E138, E139, E143, E145, E146, E147, E148-E151; F159, F164,
  F165-F172, F175-F178).** A public "73 tok/s" for Ternary Bonsai 2 measures 34.16 at best (F159). Halogen's "1,424 tok/s prefill at 32K" measures
  1,152, 5.3x llama.cpp, and the engine cannot serve our GGUF beside the resident TTS service (F165, F166). On MLCommons' own edge-agentic
  harness Atlas takes about 27% less time per turn than the llama.cpp reference, and its published Strix Halo latency is not reproduced
  (F168-F170); the vendor page's figures do not match the MLCommons entry it cites (F170). Seven recommended coding models tie with the
  incumbent through Aider (F164, F167). With a drafter added and nothing else changed, llama.cpp beats both Atlas builds on the
  MLPerf metric (F172); Atlas's own DFlash mode is 2.46x slower than its MTP mode here and the MLPerf-era source cannot serve it on HIP (F175).
  Three single-variable arms then retired the drafter's attention pattern, the vendor's own context-cap explanation and the prefix cache
  as causes (F176-F178); the DFlash collapse on this hardware is left unexplained and the investigation closed.
- **F171 qualifies F164 and F167:** every failure on task T3 across eight models carries exactly the task's seed diff, so the models' edits
  never reached the file while the transcripts claimed completion. The "opposite task profiles" are partly a harness artefact.
- **F172 qualifies F169:** the MLPerf reference implementation plus a speculative drafter (E147) takes 7,775 ms per turn against the
  reference's 12,863 and Atlas's 9,307-9,453, at identical accuracy. Atlas is faster than the reference, not than the open engine
  configured with the speculation Atlas itself uses.
- **New evidence:** results/e143 to results/e146 raw trees (Aider per-attempt records, the E146 harness reports minus their 12 MB
  conversation logs, speed-client JSONs), results/e146-gates.md, the Atlas one-line patch results/e146/w4a16-nvfp4.patch.
- **New report source:** reports/2026-09-25-vendor-claims-on-your-own-box.md and its one-pager, for the public page.

#### Changed claims (old -> new)

- (none. Five claims added under new ids; no existing value changes.)

#### Retracted claims

- (none.)

### r5.0

- **This release catches the public data up with the research: F47 to F166, 120 findings recorded after r4.6, and every
  experiment behind them.** Nothing in claims.yml changes value in r5.0 (see "Claims under review" below). Three build
  changes apply to this package and are declared in WITHHELD.md: it ships only files that git tracks, it withholds
  internal design documents, and it withholds two sets of files that contain private content (captured Claude Code
  requests, and coding transcripts that quote other repositories' source). Each is stated where it matters, not hidden.
- **Text-to-speech on this GPU (F47-F56, F133).** Engine architecture, not "AMD is slow", decides throughput: a 200x
  realtime-factor spread on one GPU (F47). vLLM does not run on gfx1151 (F48). Autoregression and model size compound to
  about 3000x (F49). Fish s2-pro returns HTTP 200 and a well-formed WAV containing 47 seconds of non-speech (F50).
  MegaTTS3 is Apache-2.0 and still cannot clone a voice locally, because the encoder is withheld (F52). Zonos builds and
  imports but cannot be brought up (F53). Zero-shot cloning has an accent-coverage limit that reference quality cannot fix
  (F54). The narrator was settled as VCTK p239 cloned by Chatterbox (F56). **F54's amendment and F52 record a
  retraction: "CosyVoice3 WORKING" was wrong, every one of its renders was garbled, and the fix that was tried is the
  likely cause. F55 then found it not viable.**
- **The platform underneath (F57-F58, F63-F64, F72, F106, F109-F111, F120, F129, F131, F135-F136, F138, F166).** The kernel
  drifted from 6.17 to 7.0 under a register that assumed one stack (F57), and the repo.radeon.com apt pin is
  load-bearing (F58). KV cache at q8_0 is free and 4-bit is a 5.6% cliff (F110). `-ub 2048` is worth 22.9% on real
  prefill (F111). The "~100K prefill wall" is a tunable, `n_ubatch`, and the finding was amended twice (F72).
  **F109 retracts the "~60 GiB" deadlock boundary: it does not exist on kernel 7.0.0-29, and neither does the contention
  trigger.** Prefill collapses with prompt length, so the context a box can hold is not the context anyone will wait
  for (F136). A maintenance window is not a clean box: TTS stays resident with 8 GiB of GPU memory (F166).
- **Knowledge work and model choice (F67-F69, F71, F73-F83, F89, F92-F94, F116, F118, F130, F140-F149, F153-F154).** Qwen3.8-27B
  beats the small workhorse on judged-free knowledge work by 6 of 20, all in the two hardest categories (F67).
  Reasoning effort is a routing axis with no middle setting on knowledge work (F69), and on coding it has an optimum
  in the middle (F71). A 3-task category produced a recommendation that inverts at 13 tasks (F73). Retrieval under
  scale is a measured strength (F74). What small models cannot do is walk a calendar (F80), and that is a fact about
  one model, not about the class (F118). Flash-Next matches the incumbent and never beats it, for 5.6x the memory
  (F116). Q4_K_M is the knee of the quantisation curve (F149). The knowledge-work banks saturate at the frontier: three
  models across a 40x price range score within one item (F153). DeepSeek-V4.1-Flash cannot be served on this box (F154).
- **Agentic coding (F97-F105, F107, F112-F115, F119, F147-F148, F152, F164).** Claude Code drives a local model with no
  translation shim (F97), and its harness floor of 44,912 tokens eliminates models before quality is asked (F98).
  The blocker for local agentic coding is tool-schema bytes in llama.cpp's grammar builder, not model capability
  (F103, F104). Aider drives both local models first try (F105) and is fast enough to be invisible (F112), but exits 0
  whether or not it did anything (F113, F152). F164 (experiment E143) tests the coding models a community chat
  recommended: four models tie on Aider passes and split the tasks in opposite ways, and the incumbent is 2x to 10x
  faster.
- **Speculative decoding and small-model designs (F84-F85, F160-F163).** MTP preserves the answer and not the completion
  (F84), and draft acceptance is a property of the workload (F85). A small model in front of the 27B does not pay: the
  draft-then-review cascade is safe and 30% slower (F161), the small model is most confident where it is wrong so it
  cannot gate (F162), and the 27B can gate itself safely but the gate costs what it saves (F163).
- **Vendor claims, tested (F120, F159, F165).** The community Strix Halo speed table verifies twice on our hardware
  (F120). A public "73 tok/s" for a 27B does not reproduce: 34.16 is the ceiling here (F159). Halogen's "~1,424 tok/s at
  32K prefill" measures 1,152, which is 81% of the claim and 5.3x llama.cpp, reproduced conditionally (F165).
- **Images (F155-F158).** Qwen-Image-2.1 runs on this box only with the gateway down and a tiled VAE decode (F155); image
  tools here exit 0 on a blank output (F158).
- **Method (F59-F60, F65-F66, F70, F79, F86, F88, F90-F91, F95-F96, F100, F117, F121-F128, F132, F134, F137, F139, F142,
  F145, F150-F151).** The lessons that cost the most: a saturated instrument cannot compare anything (F126, F142,
  F153), a deterministic grader can be reproducible and still wrong (F95), a pre-registration that names a concept
  instead of a field is not falsifiable (F65), a control must reproduce its own items before a cross-build
  comparison is licensed (F117), and one wrong defect report reached the edge of publication (F139).
- **New evidence:** the tracked raw evidence for the experiments the findings cite, and the pre-registration and results
  documents for the frontier-API, Bonsai, Halogen, cascade, gate and coding experiments (E135 to E143). Verbose
  server logs are not shipped (see WITHHELD.md); the JSON, markdown and summary files that the findings cite are.

#### Changed claims (old -> new)

- (none. No claim in claims.yml changes value in r5.0. Its header still reads release 4.0 and data_freeze
  2026-07-17: that header has not tracked package versions since r4.0, and the claims themselves were last reviewed
  against the data on 2026-07-17.)

#### Claims under review

Findings recorded after the claims were last reviewed bear on these published claims. Each stands as published
until the review is done; none is withdrawn here.

- **C-LONGCTX-USABLE, C-OP-GUIDANCE-ROCM-LEVER, C-PREFILL-ROCM-VULKAN, C-LONGCTX-FIRST-ANSWER:** F72 (the ~100K prefill
  wall is a tunable and the finding was amended twice), F111 (`-ub 2048` is worth 22.9% on real prefill), F129 (Vulkan
  did not fail under any controlled condition), F136 (prefill collapses with prompt length). This release does not
  re-measure the ROCm-over-Vulkan comparison under the tuned flags.
- **C-REASONING-TOKEN-TAX-LOCAL:** F67 and F69 (Qwen3.8-27B, a reasoning model, does document work well at low effort)
  and F140 (the reasoning-effort default is where the cost is). The claim says local reasoning models are not suited to
  structured document work; the later findings narrow that to a default-effort effect.
- **C-TOOLUSE-DOC-001, C-TOOLUSE-SERVING-001:** F76 (the tool-use instrument is five runs at temperature 0.2, so
  intermediate per-task scores do not reproduce between sessions), F93 and F94 (offering a tool is never free), F99
  (tool-calling must be measured under `tool_choice: auto`), F103 and F104 (tool-schema bytes are the serving limit).
- **C-CAPABILITY-PARITY-001:** F67 (a larger local model separates from the workhorse on judged work) and F86 (model
  evaluation and system evaluation are different measurements).
- **C-CONCURRENCY-SMALL-TEAM-P1:** F108 (`--cache-ram`, not slot count, is the multi-turn variable) and F135 (three models
  stay resident for the price of one context).
- **C-SPEED-WORKHORSE-P1:** F63 (the build and kernel move is worth about +3.3% token generation).

#### Retracted and amended findings

- F52 and F54 (amendment): the CosyVoice3 "working" result. F55 supersedes it.
- F72: amended twice on the day after publication; the "cannot prefill ~100K" conclusion is withdrawn, the evidence is not.
- F109: retracts the "~60 GiB" deadlock size boundary and the contention trigger.
- F121 and F139: recorded cases where a harness scored a run that never happened, and where a summarised page produced a wrong
  defect report.

### r4.6

- **The meeting-intelligence workstream lands: transcription accuracy, silence hallucination, and
  speaker attribution (F44, F45, F46), with two new evidence directories - results/transcription/ and
  results/diarisation/.** This is the benchmark half of a system that now runs end to end on the box:
  audio in, an attributed transcript out, nothing leaving the building.
- **F44 - Whisper fabricates speech from pure silence, and this is a REPRODUCTION, not a discovery.**
  Without voice-activity detection the model invents ~2 utterances per minute of silence (97% the
  phrase "Thank you."); VAD removes them completely (0 across 72 conditions). The phenomenon is
  well-documented prior art (Koenecke et al., FAccT 2024) and the finding says so in as many words - it
  must never be published as novel. The one reframing that is ours: by COUNT the smaller model
  hallucinates more, but by HARM the larger model is ~4.9x worse, because it emits grammatical English
  a reader cannot distinguish from real speech while the small model labels the gap "[BLANK_AUDIO]".
  Pre-registered before any run. New claim C-TRANSCRIPTION-SILENCE-VAD-001.
- **F45 - we tested our own hypothesis that smaller models transcribe better, and it is FALSE.** True
  word error rate on LibriSpeech test-clean (human transcripts, published expected value): large-v3-turbo
  2.40%, small 3.35% - large ~28% better, and ~28% better on meeting audio too. The 2.40% matches the
  model's published figure, which validates the harness. A first, batched version of the harness had
  INVERTED the answer (16.23%, "small is better") by dropping audio from concatenated files; it was
  caught only because 16.23% is impossibly far from LibriSpeech's known ~2-3%. A public benchmark is an
  instrument check, not just data. New claim C-TRANSCRIPTION-WER-001. NB: 2.40% is clean read speech and
  must never be quoted as meeting accuracy.
- **F46 - general diarisation is hard and we do not win it; the reframe to "host versus other" does.**
  Measured on AMI against real labels and pyannote 3.1: our best hybrid reaches 10.5% DER on close-talk,
  pyannote's own pipeline 6.5% - it beats us ~3x, reported plainly. Two keepers: a single distant table
  mic is within ~1 DER point of per-person headsets (21.1% vs 20.2%, against a predicted 8-point
  penalty), so an on-prem box needs no headsets (new claim C-DIARISATION-FARFIELD-001); and reframing
  the question from "separate every speaker" to the binary "is it the host or someone else" tags 97.2%
  of transcript lines correctly across four real calls from one ~4-minute enrollment - the difficulty
  inverts (more people makes it easier), and this is the abstraction meeting intelligence actually needs.
  New claim C-TARGET-SPEAKER-001.
- **New evidence:** results/transcription/ (e41/e42/e45 + the silence JSONs) and results/diarisation/
  (e43-e50 + pre-registrations). All measurements 2026-07-17; the meeting corpus is real client audio,
  gitignored and described by shape only, so the shipped evidence is the synthetic-silence and
  public-benchmark runs plus the numerical summaries.

#### Changed claims (old -> new)

- (none. F44-F46 are new measurement; no existing claim id changes value. The "smaller models
  transcribe better" idea was a working hypothesis, never a published claim - F45 refutes it before it
  could become one, which is the point of registering predictions.)

#### Retracted claims

- (none.)

### r4.5

- **New findings F42 and F43 (experiments E36, E37), and F43 CORRECTS A PUBLISHED CLAIM.**
- **F42: llama.cpp's router mode is free for concurrency.** Router versus direct serving, measured in
  one session on one build with one driver: 1.000 / 1.002 / 1.007 of direct throughput at 1 / 4 / 16
  concurrent slots, with F17's 2.66x scaling preserved. Its cost is TAIL latency, not throughput -
  median is untouched but the 95th percentile at 16 slots is 46% higher. Migration note: the native
  `/completion` endpoint requires a `model` field under the router and returns 400 without one;
  `/v1/chat/completions` callers are unaffected.
- **F43: on a Mixture-of-Experts model, sixteen people asking sixteen DIFFERENT questions get 40% less
  throughput than sixteen asking the SAME question** - 181.28 vs 108.86 tokens/sec, with prompt length
  and content class held constant and generated-token counts verified identical. A DENSE model shows no
  such penalty (-0.1%), which identifies the mechanism: MoE models route each token to a few
  specialists, so divergent requests force the machine to fetch far more of the model per step. Dense
  models read all their weights every token regardless, so batch composition cannot matter.
- **The corrected claims, and why this is not cosmetic.** The registry claimed the workhorse "scales
  aggregate throughput about 2.66 times from one to sixteen concurrent users". Sixteen concurrent USERS
  means sixteen people asking different things - exactly the condition that measurement never tested,
  because every stream in it ran the same prompt. Measured properly:

  | concurrent users | same question (published) | different questions (real) |
  |---|---|---|
  | 1 | 72.78 | 71.59 |
  | 4 | 138.93 | 121.35 |
  | 16 | 192.19 | 109.40 |
  | scaling 1->16 | 2.66x | **1.53x** |

  **Sixteen real users is slower than four.** The real curve peaks at about four and declines.
- **C-CONCURRENCY-MOE-SCALING: 2.66 -> 1.53** (unit renamed to name distinct users).
  **C-CONCURRENCY-SMALL-TEAM-P1** rewritten around the measured peak - the "small team of 3-5"
  conclusion SURVIVES and is now measured rather than extrapolated (four concurrent users is the box's
  best point, roughly 39 tokens/sec each, faster than anyone reads), but the number attached to it was
  wrong for the scenario it described. The published concurrency CHART now ships BOTH curves, because
  showing only the same-question line overstates fleet capacity by 1.78x. F17 is caveated in place.
  Single users are unaffected: this is a finding about fleets, not people.
- **The generalisable lesson:** for MoE architectures, a concurrency benchmark that fires ONE prompt
  from N threads measures expert-cache locality rather than serving capacity. The practice is correct
  for dense architectures, which is why it survived unexamined - sparkbench's own harness does what
  standard practice does.
- **New evidence:** results/router-concurrency{,-prereg}.md, results/moe-diversity{,-prereg}.md.

#### Changed claims (old -> new)

- **C-CONCURRENCY-MOE-SCALING: 2.66 -> 1.53** `times_throughput_1_to_16_users` ->
  `times_throughput_1_to_16_distinct_users`. The old value is a same-question best case; the new one is
  sixteen distinct users. Both are real; only one describes the claim's own wording.
- **C-CONCURRENCY-SMALL-TEAM-P1:** restated on measured rather than extrapolated grounds; conclusion
  unchanged (a small team is well served; ~4 concurrent users is the peak).
- Chart `concurrency-scaling`: the MoE series now ships as TWO lines (same-question and distinct-users)
  instead of one.

#### Retracted claims

- (none. F43's own earlier "output diversity" framing was corrected before it ever reached a claim id
  or a release - it appeared only in the previous release's findings register, and the correction is
  recorded inline there.)

### r4.4

- **New finding F41 (experiment E35): the box is memory-BANDWIDTH bound, so running two models at
  once splits one budget instead of adding a second - and the split is 4.6:1 against the fast model.**
  Predictions were registered before the runs. Both models sit near one bandwidth ceiling (the MoE
  workhorse activates ~3B params/token, ~1.7 GB read, for 91 t/s; dense Mistral-24B reads ~13.4
  GB/token for 15 t/s), so concurrent throughput had to divide one budget: measured normalised sum
  **1.05** against a predicted ~1.0. You do not get two models' work for one box's price.
- **The asymmetry was NOT predicted and is the operational result.** Run concurrently, the workhorse
  keeps **18.9%** of its solo speed (91.37 -> 17.28 t/s) while Mistral keeps **86.1%** (15.24 ->
  13.13). Mistral reads ~8x more per token and monopolises the bus, destroying precisely what makes
  the MoE fast - bandwidth efficiency is the MoE's whole advantage. Contended, the workhorse is
  slower than Mistral running alone. Never serve a dense model alongside the MoE on purpose. This
  also re-explains F34's "Mistral is 5-8x slower" as a bandwidth ratio rather than a mystery.
- **Load/unload is safe, and the memory cap is real.** `--models-max 2` evicts BEFORE loading - memory
  sampled every 50ms across a third model's load peaked at exactly the existing two-model level, never
  holding three - so the cap genuinely bounds peak memory against the ~60 GiB hardware edge rather
  than merely hinting. Eviction is least-recently-used; explicit unload returns memory to the system;
  an unloaded model reloads on demand in 3.3s; twenty alternating switches held 41.05 GiB with zero
  drift and no silent reloads.
- **A measurement artifact is recorded rather than buried.** The first concurrency run reported 1.37 -
  outside the predicted band, i.e. an apparent MISS implying spare headroom. It was an artifact: the
  two jobs were sized so one finished early, leaving the other running alone at full speed for 5.3s of
  a 13.0s window, and that solo tail was averaged into its "concurrent" rate. Recording a timestamp
  per streamed token and computing rates strictly inside the window where both were provably busy gave
  1.05. A throughput number measured over a window containing non-contended time is not a contention
  measurement. The false MISS would have argued for adopting concurrency on headroom that does not exist.
- **New evidence:** results/router-loadtest.md (all twelve predictions resolved) and
  results/router-loadtest-prereg.md (registered first, unedited).

#### Changed claims (old -> new)

- (none. F41 is new measurement; no existing claim id changes value. The routing guide is amended to
  warn against concurrent use of dissimilar architectures.)

#### Retracted claims

- (none new.)

### r4.3

- **New finding F40 (experiment E34): the box holds two models on call at once.** "One model at a
  time" turned out to be a property of how we launch llama-server, not of the hardware. This build
  has a router mode (launch with no model; each request names its model). Measured attended at
  production context (c=49152, 4 slots): workhorse 20.21 GiB, **both models resident 41.04 GiB**,
  switching between them **0.04s**, D-state 0 throughout. The workhorse's footprint under the router
  is identical to the production gateway's, an independent check that it allocates normally.
- **Two models is the safe cap on this box, and the default is not.** 41.04 GiB leaves ~19 GiB under
  the ~60 GiB memory edge (F24) that requires a physical power cycle to clear; a third model at
  ~20 GiB lands on it. `--models-max` defaults to 4. Related safety property: use `--models-preset`
  and never `--models-dir`, because the model store holds 100 GB+ artefacts and autoload is on by
  default - a directory scan plus autoload could load a 397B straight through the edge.
- **Per-model presets close a gap in F39's design.** serving.conf carries one global flags line, but
  models need different flags: Mistral-Small needs a chat template for tool use that the workhorse
  does not, so a swap would silently lose tool use. A preset carries `chat-template-file` per model.
- **E33/F38 independently reproduced, and a trap recorded.** Mistral-Small-3.1 on its own template
  refuses tool calls with the same refusal string E33 recorded, reached by a different serving path.
  The BUILT-IN `mistral-v7-tekken` template is a trap for this model - it produced pretraining
  garbage, F37's chat-template fingerprint from the opposite cause (a wrong template overriding a
  working one, rather than a missing one). E33's hand-written template is the one that works.
- **Not adopted, and the notes say why:** llama.cpp labels router mode EXPERIMENTAL, and concurrent
  inference against both models, sustained residency, and unload behaviour under models-max pressure
  are untested. This release records a measurement, not a recommendation.
- **New evidence:** results/router-multimodel.md.

#### Changed claims (old -> new)

- (none. F40 is new measurement; no existing claim id changes value. The routing guide
  (reports/) is amended rather than a claim - its session-vs-task advice now names its own shelf life.)

#### Retracted claims

- (none new. F39's tool-use retraction landed in r4.2 and stands.)

### r4.2

- **F39 is PARTIALLY RETRACTED, and this release exists to correct it.** r4.1 shipped F39 claiming
  that a missing `--jinja` flag had left the production gateway unable to do tool use - so F38's
  office-tool capability (workhorse, 91%) had been unavailable at the endpoint users reach for the
  whole period it was reported. **That was never measured, and it is false.** `--jinja` defaults to
  ENABLED on this llama.cpp build (v200, 067de93), so production always had the chat-template path.
  A direct control on 2026-07-17 served the same model WITHOUT the flag and got identical structured
  `tool_calls` (results/tool-use/jinja-default-control.md, new evidence in this release). Anyone who
  read r4.1's F39 should discard that half of it.
- **What F39 got right, and still gets right:** the production unit omitted `-c`, so llama-server
  allocated the model's full 262144-token trained context - about 22 GiB of KV. Setting `-c 49152`
  (48K x 4 slots, E30's measured envelope) reclaimed **19.70 GiB**, measured before and after
  (GTT 39.91 -> 20.21 GiB). The three-writer flag problem was also real: the next model swap would
  have silently reverted that fix.
- **HARNESS-RULES Rule 8 gains a second half** as a direct result. The rule said a benchmark measures
  a CONFIG, not a box - name the config a finding needs and assert production against it. It now also
  says: claiming a config difference MATTERS is itself a claim that needs measuring, so run BOTH
  configs. A flag's presence in a command line is not evidence of its effect - a default can make it a
  no-op - and a harness docstring saying "must be served with X" describes the harness, not the
  server without X. The rule's own flagship example was the thing that broke it.
- **New evidence:** results/tool-use/jinja-default-control.md (the with/without control).

#### Changed claims (old -> new)

- (none. The retracted material never reached claims.yml - no claim id asserted it. C-TOOLUSE-*
  describe E33's per-model template finding, which is unaffected and stands.)

#### Retracted claims

- No claim id is retracted, but **F39's tool-use half is** - see above. The finding text in
  FINDINGS.md now carries the retraction inline rather than being silently rewritten, so a reader who
  saw r4.1 can tell what changed and why.

### r4.1

- **New finding F39 - the benchmarked config was not the served config.** Every tool-use number in
  E32/E33 was measured against a llama-server started with `--jinja`; the production gateway ran without it,
  so the office-tool capability F38 reports was unavailable at the endpoint users actually reach. The same
  unit omitted `-c`, allocating the served model's full 262144-token trained context. Fixed and measured:
  n_ctx 262144 -> 49152, GTT 39.91 -> 20.21 GiB (19.70 GiB reclaimed), tool use verified at the production
  endpoint (7/7 valid calls; the no-tool trap correctly declined), throughput 88.04 t/s with no regression.
  F39 also records the mechanism - the serving flags had three writers, so any fix would have been silently
  reverted by the next model swap.
- **Evidence integrity:** F37 v1's cited evidence had been silently overwritten in place by the v2 run
  (two homes for one run). v1 restored from git; the harness now refuses to overwrite existing evidence.
  The fine-tune results' canonical home is results/finetune/ (duplicates in results/real-quality/bigmodel/
  removed - same dedup precedent as r4.0's raw sweep).
- **The completeness gate was not gating (fixed).** It accepted a cited path whenever any file of that
  basename existed anywhere in the package, never read the evidence docs' own citations, and could not
  see .log paths at all. All three closed and proven in both directions. Readers of prior packages should
  know the check's PASSED was weaker than advertised; this release's is not.
- **New evidence:** results/tool-use/results-prod-config-verify.json (the production proof run);
  results/tool-use/coder-native.log (cited by E33 since it was written, but gitignored until now - a
  clean clone could not previously reproduce that claim).

#### Changed claims (old -> new)

- C-QUALITY-SENDREADY-001 and C-QUALITY-GROUNDED-001: evidence path
  `results/real-quality/eval-pilot.md` -> `docs/FINDINGS.md`. The old path NEVER existed (a mashup of the
  results/real-quality/ evidence directory and the unrelated results/eval-pilot.md); it went unnoticed
  because the old gate matched on basename. The claims' VALUES and statements are unchanged - this is a
  citation correction, not a measurement change.

#### Retracted claims

- (none active; retractions remain in FINDINGS.md history where applicable.)

### r4.0

- **Architecture change:** sparkbench no longer produces HTML. This package is the sole deliverable -
  reference markdown, the findings register, the claims registry (claims.yml), and all evidence directories.
- **New evidence directories now shipped** (previously absent from the HTML delivery): results/real-quality/,
  results/tool-use/, results/finetune/, results/coding-screen/, plus tools/cost_model.py (every cost claim cites it).
- **New claims:** C-TOOLUSE-DOC-001, C-TOOLUSE-SERVING-001, C-TOOLUSE-CONDITIONAL-001 (back the tool-use headline).

#### Changed claims (old -> new)

- (none this release; cost figures reconciled to tools/cost_model.py in the prior cycle.)

#### Retracted claims

- (none active; retractions remain in FINDINGS.md history where applicable.)

## Completeness

Every path cited by FINDINGS.md, experiments.md, claims.yml, and the results/ evidence documents exists
in this package - the build fails otherwise. Internal plans and briefs are excluded from that rule: they
record intent, not evidence, and legitimately reference runs that were proposed and never produced.

Exception, declared: the paths listed in WITHHELD.md are cited but not shipped, each with its
reason (internal design documents; files the source repository keeps out of git).
