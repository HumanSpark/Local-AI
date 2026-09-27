# E90 pre-registration - Aider as an everyday local coding workflow

**Written 2026-08-30, before any task ran.** Amendments below this line are dated and
declared before the runs they affect (HARNESS-RULES, "pre-register predictions").

## What this is, and what it is not

This is **not** a model bake-off and not a hardware question. Both are closed:
E88/F106 settled that sparkmax is at or above its hardware class, and E89 settled the
serving configuration. The single open question is whether **Aider driving the resident
production model is a workflow the owner can rely on day to day**.

One arm. One model. One endpoint. Nothing is being compared to anything.

## The configuration under test - discovered live, not recalled

Read from the running server on 2026-08-30 08:1x, not from prior notes:

| item | value | source |
|---|---|---|
| model id | `/opt/models/staging/Qwen3-30B-A3B-Instruct-2507-Q4_K_M.gguf` | `GET :8400/v1/models` |
| build | `b9865-067de9371` | `GET :8400/props` |
| context | `n_ctx` 98304 of `n_ctx_train` 262144 | `GET :8400/v1/models` |
| slots | 4, auto (no `-np`) | `GET :8400/props` + `ps` |
| serving flags | `-c 98304 -fa on -ctk q8_0 -ctv q8_0 --jinja --host 127.0.0.1 --no-webui -ub 2048` | `ps -o args= -C llama-server`, PID 1385933 |
| Aider | 0.86.2, user-level | `aider --version` |

**Endpoint: `http://127.0.0.1:8499/v1`**, which is `tools/aider_probe.py` forwarding to the
production `llama-server` on `127.0.0.1:8400` - the same process, the same weights, the same
flags. Measured proxy cost on a 15-token request: proxy-side TTFB 0.1357 s against
client-side 0.1519 s.

### Declared deviation - the authenticated door is not the one being used

The goal named "the real SparkRouter endpoint". The authenticated door
(`http://<fleet-host>:8000/v1`) **cannot be driven from this account**, and that was probed
rather than assumed:

- `GET :8000/v1/models` unauthenticated returns **HTTP 401**; `/health` returns `200 {"state":"serving"}`.
- The gateway reads its keys from `/var/lib/sparkrouter/keys.txt`, which is `0750 spark-infer`.
  `open()` as `agent-spark` raises `PermissionError` (errno 13).
- `SPARKCORE_LLM_SPARKMAX_API_KEY` is **not** in this host's vault checkout:
  `vault_get.py` exits 1, and `/opt/sparkvault/apps/*.sops.yaml` carries only four names
  (`FORGEJO_SVC_SPARKMAX_TIER_A_TOKEN`, `FORGEJO_SVC_SPARKMAX_TIER_B_TOKEN`, `HF_TOKEN`,
  `SPARKCORE_LLM_OPENROUTER_API_KEY`). A narrow grant is deliberate and is not to be widened.

So every figure here is **loopback**, and the Caddy plus auth-sidecar hop is **unmeasured**.
Any number quoted for a client on sparkline must carry that gap explicitly.

## The tasks - real open defects in this repository, run in disposable worktrees

Toy prompts were rejected. All three are defects sparkbench actually has right now; two of
them are already listed as open in `HANDOFF.md`. Each runs in a fresh `git worktree --detach`
off `HEAD`, thrown away afterwards.

| task | kind | the real defect |
|---|---|---|
| **T1** | small bug fix, 1 file | bare `python3 -m pytest` at the repo root aborts: it descends into the vendored `llama.cpp/` tree and dies on `ModuleNotFoundError: No module named 'appium'` |
| **T2** | test-driven, test held read-only | `tests/test_sparkrouter_discovery.py` (13 assertions, written first, red at `rc=2`) specifies `tools/sparkrouter_discovery.py`, which does not exist |
| **T3** | bounded multi-file, 2 files | `tests/test_auth_sidecar.py` and `tests/test_kokoro_gateway.py` import `fastapi` at module level; it is absent, so two files abort collection of all 731 tests |

**Scoring is a before/after gate, not a judgement.** Each task carries a `verify` command that
must exit non-zero before Aider runs and zero after. A task whose verify already passed
beforehand scores `invalid-precondition`, never `pass` - a control that cannot fail is not a
control (E89's method note).

**T2's test is passed with `--read`, not as an editable file.** A TDD arm that can rewrite its
own specification is measuring nothing.

**Aider runs at its defaults** - no `.aider.model.settings.yml`, no edit-format override, no
repo map tuning. The question is what the owner gets out of the box; tuning it first would
answer a different question. Aider selected the `whole` edit format on its own, because this
model id is unknown to litellm.

## Predictions - each names the field it is scored against

Field paths are into the runner's results JSON (`results/raw/e90/tasks.json`).

- **P1** - T1 completes. Field: `T1.outcome == "pass"`.
- **P2** - T3 completes. Field: `T3.outcome == "pass"`.
- **P3** - **T2 does NOT complete on the first attempt.** 13 assertions across two public
  functions, from a specification the model may only read, is a harder ask than either edit
  task. Field: `T2.outcome != "pass"`. Scored on the FIRST run only; a later retry is a
  separate observation and does not rescue this.
- **P4** - first-turn latency stays under 10 s on every task. Field: `first_turn_ttfb_s < 10.0`
  for all three. Basis: F105 measured Aider sending 761 tokens where Claude Code's floor is
  44,912, and E88's context curve puts 1,024 tokens at 0.93 s.
- **P5** - first-turn prompt is under 5,000 tokens on every task. Field:
  `first_turn_prompt_tokens < 5000`. This is the prediction that decides whether the workflow
  is usable at all: E88 measured 4,096 tokens at 4.37 s and 46,000 at 177.39 s.
- **P6** - no task needs more than 4 model requests. Field: `n_requests <= 4`.
- **P7** - no task edits a file it was not given. Field: `files_touched` is a subset of
  `files_given` for all three. This is the safety prediction; a local model wandering outside
  its brief is the thing that would make the workflow undependable.

## Amendments

### Amendment 1 (2026-08-30, after run 1, before run 2) - the gate was broken, not the model

Run 1 scored all three tasks `invalid-precondition`. That was **my instrument**, three
separate defects, and none of them a model result:

1. **Every `verify` lost its exit status through a pipe.** `pytest ... | tail -12` reports
   `tail`'s status, so a failing command scored zero. This is the trap named in
   `shell-and-command-safety.md` rule 2, walked into anyway. Fixed by running seed and verify
   under `bash -o pipefail`.
2. **A new file produced no diff.** `git diff HEAD` ignores untracked files, so T2's entire
   output - the implementation it was asked to write - was recorded as an empty diff and then
   destroyed with the worktree. Fixed with `git add -A -N` before diffing.
3. **T1's precondition could not exist in a worktree.** `llama.cpp/` is gitignored, so a fresh
   worktree has no vendored tree to descend into and the defect cannot reproduce. Fixed by
   seeding the worktree with the same vendored shape
   (`llama.cpp/scripts/snapdragon/qdc/tests/conftest.py` doing `from appium import webdriver`).
   This recreates the real condition rather than inventing one.

Additionally, `tests/test_sparkrouter_discovery.py` was committed to `HEAD` in its red state
before T2's implementation existed, so it contaminated T3's collection count. T3's verify now
carries `--ignore` for that one file.

**What run 1 still legitimately observed**, because these come from the commands' own output
rather than from the broken return codes:

- **T2 went red to green.** `verify_before_tail` shows
  `ModuleNotFoundError: No module named 'sparkrouter_discovery'`; `verify_after_tail` shows
  `13 passed in 0.01s`. **P3 is falsified.**
- **T1 produced a plausible but inert fix**: `pytest.ini` containing `[tool:pytest]`, which is
  the `setup.cfg` section header. In `pytest.ini` the header must be `[pytest]`, so the file
  is silently ignored. Aider reported `Applied edit to pytest.ini` and exited 0.
- **T3 touched no files at all.** The `whole` edit format stalled part-way through rewriting a
  56-line file (`25 / 56 lines 45%`), aider discarded the incomplete edit, then spent a second
  5.9k-token turn replying that the changes were "complete and correct". `files_touched: []`.
- Latency: first-turn TTFB 1.64 s / 3.54 s / 3.52 s, first-turn prompt 1,516 / 3,346 / 3,113
  tokens, 1 / 3 / 2 requests. **P4, P5 and P6 all hold on run 1.**

Run 2 re-runs all three with the gate repaired. P3 is **not** re-scored - it was decided on
run 1 and a repeat cannot rescue it.

### Amendment 2 (2026-08-30, before run 3) - the edit format is a configuration question

T3's failure was not reasoning: the model wrote a correct-looking change and the **client**
lost it. Aider chose the `whole` edit format on its own, because this model id is unknown to
litellm, and `whole` streams an entire file per edit. That is a client configuration the owner
would set once, and the goal explicitly covers configuring Aider against this model.

So run 3 repeats the same three tasks with `--edit-format diff` and changes nothing else.
This is **not** a bake-off arm: both runs use one model, one endpoint and one set of weights.
It scores a client setting, and the deliverable is a default to write down.

Prediction, declared before run 3: **P8** - `diff` completes T3 where `whole` did not, and
cuts total prompt tokens. Fields: `T3.outcome == "pass"` and `T3.total_prompt_tokens` below
run 2's.

## Stop conditions

- If P5 is falsified in the wrong direction (first-turn prompt over ~20,000 tokens), the
  workflow is not viable at defaults and the finding is the prompt size, not the model.
- If P7 is falsified, that is reported as the headline regardless of how many tasks passed.
- No task is re-run to get a better number. A retry is recorded as a retry.
