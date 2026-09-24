# Harness hard rules (Phase B design constraints)

<!--
File: HARNESS-RULES.md
Purpose: Non-negotiable design rules for the sparkbench harness, promoted from Phase A findings.
Project: sparkbench | Date: 2026-07-03
#
# Overview: Each rule carries its provenance (the Phase A evidence that
# created it). Rules here bind Phase B design and any promptfoo adoption
# decision: a tool that cannot satisfy them fights the requirements, per
# WORKPLAN 4.7. Append new rules with Why + Trigger; never delete - supersede
# with a note.
-->

## Rule 1: No harness code path ever invokes llama-cli

All model interaction goes through llama-server's OpenAI-compatible HTTP
API (or llama-completion for raw completions if ever needed). llama-cli is
a human-facing chat TUI, permitted only for manual, attended smoke checks.

- **Why:** At pinned commit 067de937, llama-cli is chat-first:
  `--no-conversation` is refused ("use llama-completion instead") and a
  closed/EOF stdin loops forever printing chat prompts - a silent hang, the
  exact failure mode WORKPLAN Section 7 requires to be loud.
- **Trigger:** Phase A step 4a first run hung exactly this way
  (2026-07-03, docs/PHASE-A-LOG.md step 4a entry).

## Rule 2: Every subprocess the harness spawns has a timeout

No exceptions: server startup, health polls, eval requests, shutdown.
A hung subprocess must become a loud, recorded failure, never a stalled
unattended run.

- **Why:** Same incident as Rule 1 - the hang produced 512KB of prompt
  spam and an immortal process instead of an error. Section 7's acceptance
  criteria require deliberate-kill scenarios to fail loudly; timeouts are
  the mechanism.
- **Trigger:** Phase A step 4a first run (2026-07-03).

## Rule 3: Offload verification reads verbose logs, not throughput vibes

The "full GPU offload / no CPU fallback" gate greps `-v` server logs for
`load_tensors: layer N assigned to device` lines: the pass condition is
zero layers assigned to CPU. A nonzero `CPU_Mapped model buffer` alone is
NOT fallback (token embeddings are host-mapped by design).

- **Why:** Default (non-verbose) llama-server/cli logging at this commit
  suppresses layer-assignment lines entirely - the gate would silently
  pass on no evidence. Throughput heuristics can't distinguish partial
  offload on small models.
- **Trigger:** Phase A step 4a needed a `-v` rerun to produce any offload
  evidence; 4b criteria (2026-07-03).

## Rule 4: Model downloads are explicit and manifest-recorded

Downloads use explicit URL fetch (curl/urllib) into /opt/models/staging,
recording repo, revision (HF API sha at fetch time), size, and SHA256 in
manifests/MANIFEST.md before first use. llama.cpp's `-hf` fetch path is
compiled out (LLAMA_CURL=OFF) so this cannot be bypassed by accident.

- **Why:** WORKPLAN 4.6 provenance discipline; `-hf` caches outside the
  two-zone store and records nothing.
- **Trigger:** Declared deviation in docs/PHASE-A-LOG.md step 3 entry
  (2026-07-03).

## Rule 5: Never re-create the amdgpu SDMA deadlock's KNOWN triggers during routine benching

The amdgpu suballocator deadlock (F24, F27, F28 in docs/FINDINGS.md) is
unkillable - a D-state task wedged in the kernel `drm_suballoc_new` path,
which SIGKILL cannot touch - and recovery requires a **hard power cycle**
(needed for BOTH F27 and F28; a graceful `sudo reboot` stalls on the
wedged task and leaves the box unreachable). Its full cause is NOT solved;
what is known is a set of triggers we must not hand it during ordinary
runs. During routine benching:

1. **Never run heavy disk I/O concurrently with a near-edge GPU model
   load.** This is the ONE *confirmed* trigger (F24, `dmesg`-verified: the
   VM-update SDMA job suballocator starved), and the only one **reproduced
   on demand** (cause-isolation Run 1b, 2026-07-10). Structurally enforced
   already by the strict-sequential download policy (zero download/hashing
   activity during any bench). Do not weaken that policy; do not `sha256sum`
   a large file while a model is loading. **Mechanism refinement (Run 1b):**
   the operative driver is MEMORY PRESSURE from the concurrent I/O evicting
   model pages faster than they load (total footprint exceeds 128 GB RAM),
   not disk I/O per se; the confirmed live signature is VRAM parking at
   exactly 2.00 GiB (2,147,483,648 B) while RSS collapses toward ~50 MB and
   `/proc/<pid>/wchan` sits at `drm_suballoc_new`.
2. **Never immediately retry a leg that just crashed with a clean GPU
   error** (`vk::DeviceLostError` / OOM, rc=134). Wait for VRAM to return
   to idle baseline (~148 MB) AND treat the retry as part of the
   failure-repro phase, not a routine re-run - do not fire it back
   automatically. This is the F28 candidate trigger: an immediate
   post-crash retry deadlocked even though the intervening idle check
   looked clean. Unconfirmed as causal (n=1), but free to avoid and it is
   exactly what produced the third occurrence.
3. **One model on the GPU at a time.** Keep `llama-gateway.service` PAUSED
   for the whole benching window (`systemctl --user stop
   llama-gateway.service`; it auto-restarts on every reboot and re-loads
   the 30B, so re-pause it after any boot). Reduces concurrent GPU/driver
   state churn.

**Honest scope of this rule:** F27's exact trigger is genuinely
unexplained (it recurred with no concurrent I/O, on the model with the
MOST headroom in its batch). This rule avoids the *known* triggers during
*routine* work; it does NOT claim the deadlock is eliminated. The
repeatability campaign's failure-repro phase
(docs/plans/2026-07-09-repeatability-campaign-plan.md, Phase 3)
*deliberately* tries to reproduce this class - that phase is exempt from
this rule by design, and whoever runs it must confirm GPU health
immediately beforehand and have hard-power-cycle access lined up (2-for-2,
a graceful reboot will not come back on its own).

- **Why:** Three occurrences (F24 2026-07-08, F27 2026-07-09, F28
  2026-07-10) each cost a reboot; the last two cost a *hard* power cycle
  and physical presence. Two of the three were reachable via avoidable
  operator behaviour (concurrent heavy I/O; immediate post-crash retry) -
  cheap to not repeat.
- **Trigger:** F28 (2026-07-10), an immediate retry of Command A+'s d8192
  leg right after it crashed cleanly, deadlocked the box for the third
  time - prompting Alastair to require the triggers be documented so we do
  not re-cause them. See docs/FINDINGS.md F24/F27/F28.

## Rule 6: Bank both sides of every risky test

Commit AND push immediately BEFORE any deadlock-capable or near-edge leg
(clean tree: pre-registration, prior results, docs on forge) and
immediately AFTER it (raw results + entry + touched reports) before
anything else runs. Forge must always tell the whole story if the box
wedges mid-test. `tools/banking_audit.sh` is the gate (AUDIT-PASS or fix
what it lists). Origin: Alastair, 2026-07-11, twice-stated during the
deeper-research campaign; enforced through E29-E31 and the E30 envelope
climb.

## Rule 7: Audit the grader before believing a surprising score

When results look implausible (a frontier model losing to a cheap one,
zero passes across every model, identical totals from different models, a
"stability ceiling" below banked evidence), inspect the actual transcripts
/ outputs / server logs BEFORE the number enters any record as a model
property. A score is a property of model + prompt + serving configuration
+ output budget + extraction policy + grader TOGETHER (F29): in one
campaign, eight successive corrections were all in the measurement stack,
not the models. Corollaries: never launch a server with stdout/stderr
discarded (the E30 phantom ceiling); pre-registered predictions that miss
in an implausible pattern are a grader-audit trigger, not a headline.

## Rule 8: A benchmark measures a CONFIG, not a box - assert production against it

Rule 7 says a score is a property of model + prompt + serving config +
budget + extraction + grader together. Rule 8 is its deployment half: when
the harness sets its own serving flags, the harness and production drift
silently, and NOTHING in the results can detect it - the numbers stay
perfectly true of a configuration nobody serves.

So: any capability finding MUST name the serving configuration it requires,
and production MUST be asserted against that configuration before the
finding is reported as a property of the box.

F39 is the instance: the production unit omitted `-c` and allocated the
model's full 262144 trained context (~22 GiB of KV; 19.70 GiB reclaimed by
setting it), and the serving flags had three writers, so the next model swap
would have silently reverted the fix.

**And F39 is also the counter-example, which is why this rule has a second
half.** Its original write-up ALSO claimed that a missing `--jinja` had left
tool use disabled in production. That was never measured - the pre-fix config
was never run, and `--jinja` turns out to default to ENABLED on this build, so
the flag was a no-op and tool use worked all along (retracted 2026-07-17;
control: results/tool-use/jinja-default-control.md). The rule's own flagship
example contained an unmeasured claim about a config difference.

So the second half: **asserting that a config difference MATTERS is itself a
claim that needs measuring.** Comparing two configurations means running BOTH.
A flag's presence in a command line is not evidence of its effect - a default
can make it a no-op - and a harness docstring that says "must be served with
X" describes the harness's invocation, not the server's behaviour without X.
Test the config you claim is broken, or do not claim it.

Corollaries:
- **Serving flags have exactly ONE writer.** Since the sparkrouter graduation
  (2026-07-19) they live in sparkrouter's ACTIVE `/var/lib/sparkrouter/serving.conf`,
  read by BOTH systemd (EnvironmentFile) and the gated model_swap.sh - which is
  the only sanctioned writer. NEVER inline flags into a unit's ExecStart and
  never let any other script sed them in: F39 had three writers, so any fix to
  the unit would have been silently reverted by the next model swap. sparkbench
  benches raw llama-server with its OWN build, never through the relay.
- **A blue/green health check must use the production flags**, or it
  validates a configuration that never ships.
- `-c` is mandatory (see the llama-server rule in CLAUDE.md) - that one is
  measured. `--jinja` is explicit-but-redundant on this build; keep it for
  legibility, but do not believe it is load-bearing without re-testing.

## Rule 9: One GPU consumer at a time - a contended number is VOID, not noisy

The box has one GPU. Any second consumer - another `llama-bench`, another
`llama-server`, the sparkrouter gateway - makes BOTH measurements void. Not
degraded, not noisy: void, because neither process can say what share it got.

1. **Every bench entry point refuses to start** if `llama-server` OR
   `llama-bench` is already running. Checking only one of the two is the gap
   that caused the 2026-08-15 incident (F64).
2. **The relay comes down under the advisory maintenance flag** for any run
   whose number will be quoted - `tools/relay_bench_window.sh`.
3. **A contended result is deleted, not archived**, unless it is being kept
   as evidence for a finding - and then it is labelled as such at the point of
   storage, never left to look like a measurement.
4. **Between an operator-run and a session-run, confirm which one is live
   before starting anything.** The guard is a backstop, not a plan.

## Rule 10: Every model benchmark includes a concurrency sweep

Single-stream `tg128` is one point on a curve, and on this hardware it is the
LEAST representative point: single-stream generation does not saturate the
GPU. Quoting it alone systematically understates what the box can deliver.

**A model benchmark is not complete until it has an aggregate-throughput
figure at more than one slot count.** Minimum sweep: `-np` in {1, 2, 4, 8} via
`tools/serve_bench.py`, which owns the server lifecycle and the Rule 3 gate.

Report BOTH quantities, always:

- **aggregate** = delivered tokens / wall clock. Charges TTFT and queueing.
  This is what a user experiences.
- **capacity** = mean per-stream rate x streams. Steady-state generation.
  This is what the silicon can do.

They diverge sharply on slow models (Qwen3.8 at 8 slots: aggregate 2.85x,
capacity 2.94x, but TTFT p50 4x worse than at 1 slot), and quoting whichever
is larger is how a concurrency claim gets overstated.

**Honour the harness's `under_sampled` flag.** A 45s window at a low
per-stream rate yields too few requests per stream to trust; raise
`--duration` and re-run rather than quoting a flagged point.

Origin: F64. The concurrency headroom on this box was discovered by ACCIDENT,
via a collision between two benches, after a year of single-stream numbers.

## Rule 11: No arm starts until the context is PROVEN to fit

When a prompt plus its generation budget exceeds `-c`, llama-server does not
error. It drops tokens off the FRONT of the context, so the model answers from
a brief whose opening documents are gone, and that answer grades as a
capability failure. Nothing in the output looks wrong. This is Rule 7's
failure with the grader removed - there is no surprising score to audit,
because the score is exactly what a genuinely weaker model would produce.

**Every runner asserts, before its first request, that the LONGEST prompt plus
`--max-tokens` fits inside `-c`, and refuses to start when it does not.** One
overflowing question is enough to void an arm, and the arm's own summary will
not show it. `tools/bench_context.py` owns the check for all four runners.

**Tokens come from the server's own tokenizer, never from characters.** E41's
AMENDMENT 1 argued an overflow from a chars-per-token estimate and was wrong by
4,392 tokens - the pack it rejected would have fit with 3,359 to spare. The
ratio is corpus-dependent (measured 3.65 on dense contract text, 4.43 on
distractor boilerplate) and E52 then measured two Qwen generations tokenizing
one identical pack **3.3% apart**. No constant can decide whether a pack fits.

**A runner that attaches to a server it did not start must ASK what `-c` is**,
not assume one. `bench_context.server_context()` reads `/props`. A preflight
that invents the number it checks against is worse than no preflight, because
it reports a pass. Where the check genuinely cannot run - a hosted gateway that
manages its own context - record that it was SKIPPED, never a pass.

**The preflight record goes in the result file.** `context_preflight` carries
the measured longest prompt, the budget, what was needed and the headroom, so a
later reader can see the arm had room rather than trust that someone checked.

Origin: 2026-08-17. Three of the four runners had no check at all, and wiring
it found a default pairing in `run_writing_eval.py` - `--ctx 16384` with
`--max-tokens 16384` - that could not fit any prompt at all. No published
result was affected, because every recorded invocation happened to pass `--ctx
32768` explicitly. **That is the whole lesson: a default nobody uses is a
default nobody checks**, and it sat there until something made a runner start
at its own defaults.

## Rule 12: A corpus is only disjoint from the answer key it was BUILT against

Reusing an existing corpus as filler, distractors or padding for a NEW tier
requires re-asserting figure disjointness against the NEW tier's answer key,
mechanically, before the first run. Disjointness is not a property of the
corpus. It is a property of the corpus AND the key it is paired with, and it
does not travel when either changes.

**Why this is worse than an ordinary collision.** A distractor that happens to
carry a real answer makes a WRONG-DOCUMENT answer grade as **correct**. There is
no surprising score to audit, because the score is exactly what a model that got
it right would produce - so Rule 7 cannot catch it and Rule 11 does not apply.
It is the same silent class as those two, with the detector removed.

The check is cheap and must be mechanical, never a reading:

1. Derive the protected set from the graded turns themselves, so a question
   added later is protected the moment it exists.
2. **Union it with every distinctive figure in the real pack**, not just the
   answers. An operand of an answer - an insurance limit, a base fee - is a
   wrong-document trap that the answer key cannot name, because no question asks
   for it directly.
3. Exclude only what is deliberately inside the filler: the answers to questions
   ABOUT the filler, and the wrong-document traps themselves.
4. Bound "distinctive" by magnitude and by year, or clause numbers and dates
   flag every document and the check is discarded as noise.
5. Require the filler's own key figures to be unique ACROSS the selection too, or
   a question naming one document has an answer another document also supports.

**Assert that the excluded item WOULD have collided.** An exclusion justified
only by a comment rots into decoration the first time someone edits the list.

- **Why:** E56 reused the L3 distractor corpus, built disjoint from the L2/L3
  key. **DIS-05's monthly retainer is EUR 27,600 - exactly the November fee the
  new tier's A4 anchor asks for**, so a wrong-document answer would have scored
  correct on the single question the tier most wanted to catch that failure on.
  A second defect in the same pass: DIS-10 reuses DIS-02's retainer and cap, and
  taking the first ten ids in declaration order picked up that pair, which would
  have made one question ambiguous and two traps unattributable.
- **Trigger:** both found by a mechanical check while building E56 (2026-08-17),
  neither by reading the corpus. Enforced by
  `tools/validate_conversation_long.py`, which also asserts the DIS-05 collision
  would have happened.

## Rule 13: A truncated item is NOT a wrong answer, and no run may score one

Any eval runner that can hit a token cap MUST count truncated items, record the
count and a `truncation_gate` field in its output, and **exit non-zero rather
than report a score** when the count is above zero. An explicit
`--allow-truncation` records the run anyway and marks the gate `OVERRIDDEN`,
the same shape as `--allow-busy-gpu`.

- **Why:** a truncated item was never answered. Folding it into the score
  reports the TOKEN BUDGET as though it were the model's capability, and the
  resulting number is indistinguishable from a real measurement. This is the
  vacuous-success class applied to a per-item outcome, and the evidence
  doctrine already separates the two observations: `empty != unavailable`.
- **Trigger:** E92, 2026-08-31. Kwaipilot KAT-Coder scored **0 of 8** on the
  expert coding bank; 7 of the 8 outcomes were `truncated` with
  `finish_reason: length`, `completion_tokens` exactly at the cap and empty
  content. Nemotron-3-Nano lost 3 of 15 l4 items the same way, and **all three
  were in the walked-period categories the experiment's hypothesis was scored
  on**, so its 5/8 was a floor reported as a score. Same session, the same
  shape had already appeared twice: F71 records 100,000 tokens burned over
  2h 46m producing nothing, and the Flash-Next sanity load returned
  `finish_reason: length` with empty content at its template's default effort.

**The repair is tokens, and the obvious alternative is a trap.** Raising
`--max-tokens` (with `--ctx` raised to fit it) keeps the model in its measured
configuration. Reaching for an effort flag instead is only valid if the model's
chat template actually references it: **neither Nemotron nor Kwaipilot's
template contains `reasoning_effort`**, so `--thinking low` would have been
silently inert while the result file recorded `thinking: low` as applied. Check
the GGUF's embedded template before using an effort flag to fix a budget
problem - this is F39's inert-flag class and E89's `-np` explicit-vs-auto in a
new place.

## Rule 14: An item whose answer never ARRIVED is not a wrong answer either

Any eval runner that makes a request per item MUST count `transport_failed`
items, record the count and a `transport_gate` field in its output, and **exit
non-zero rather than report a score** when the count is above zero. An explicit
`--allow-transport-failures` records the run anyway and marks the gate
`OVERRIDDEN`, the same shape as `--allow-truncation` and `--allow-busy-gpu`.

**Exit 4, not 3.** Rule 13 owns exit 3. A caller branching on the status must
be able to tell a truncated run from an unanswered one, because they need
different fixes: truncation is repaired with tokens, transport failure is
repaired by finding out why the server stopped answering.

- **Why:** this is Rule 13's class one layer out. Rule 13 catches an answer cut
  off at the token cap; this catches an answer that never arrived at all.
  Both mean the model was never asked, or its reply was lost - and in both
  cases folding the item into the denominator reports the TRANSPORT as though
  it were the model's capability. `empty != unavailable`, again.
- **Trigger:** E97, 2026-08-31, by deliberate fault injection rather than by
  an accident this time. A fake server killed after answering 3 of 20 items
  produced `correct: 1, total: 20` at **exit 0** with a **PASSING** truncation
  gate. Nothing in that file distinguishes it from a model that sat the whole
  bank and got 19 questions wrong. A malformed 200 OK - valid JSON with no
  `choices` key - did the same thing at 20 of 20.
- **What it would have caught.** 17 committed result files carry
  `transport_failed` items. The severe ones were caught, but by a PERSON
  noticing and writing it down - E61's decode hang and E33's destroyed re-run
  are both documented in terms. The defence was attention, not machinery,
  which is exactly what Rule 13 replaced for truncation.
- **The known confounded case.** Four E37 Qwen3.8 cloud arms dropped 13, 1, 9
  and 8 of 20 requests and were quoted as `6/20, 19/20, 11/20 and 12/20` in
  `reports/2026-08-16-technical-complete-summary.md`. Among completed items
  they scored 6/7, 19/19, 11/11 and 12/12, so that spread is transport, not
  model non-determinism. **F66 itself is unaffected and stands** - its evidence
  is `gemini-3.7-flash` and `solar-pro4`, and all six of those arms have zero
  `transport_failed`.

**Do not "fix" a transport failure by re-running until it passes.** A run that
fails this gate has an unexplained cause - a dead server, a timeout below what
`--max-tokens` needs (E33), an upstream error envelope. Find the cause; a green
re-run with the cause still present is a coin flip recorded as a measurement.
