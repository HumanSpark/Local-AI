# E90 - Aider on the resident workhorse: fast enough, honest about nothing

**Date:** 2026-08-30 · **Pre-registration:** `results/e90-prereg.md` (two amendments declared
mid-session, both before the runs they affect) · **Raw evidence:** `results/raw/e90/`

**The question.** Not which model, and not how fast the box is - E88/F106 closed the hardware
branch and E89 closed the serving configuration. The only thing left open was whether Aider
driving the resident production model is a workflow that can be relied on day to day.

One model. One endpoint. One set of weights. Nothing is compared to anything.

## What was under test, discovered live

| item | value | how it was read |
|---|---|---|
| model | `Qwen3-30B-A3B-Instruct-2507-Q4_K_M.gguf` | `GET :8400/v1/models` |
| build | `b9865-067de9371` | `GET :8400/props` |
| context | 98,304 of 262,144 trained, 4 slots, auto | `/v1/models` + `/props` |
| flags | `-c 98304 -fa on -ctk q8_0 -ctv q8_0 --jinja -ub 2048` | `ps`, PID 1385933 |
| Aider | 0.86.2 | `aider --version` |

Nothing here was recalled from notes. `tools/sparkrouter_discovery.py` now does this read as a
tested function, and `tools/local-code` calls it before every run, so an invocation cannot
drift from what is resident.

**The endpoint is loopback, and that is a declared gap.** The authenticated door
(`<fleet-host>:8000`) cannot be driven from `agent-spark`: it returns 401, `keys.txt` is
`0750 spark-infer` (`PermissionError`, errno 13), and the key is absent from this host's vault
checkout (`vault_get` exits 1; only four names are present, none of them the gateway key). That
grant is deliberately narrow and was not widened. So every figure below is measured against the
production `llama-server` process directly, and **the Caddy plus auth-sidecar hop is
unmeasured**. Instrumentation cost, measured rather than assumed: 0.1357 s proxy-side against
0.1519 s client-side on a 15-token request.

## The three tasks

All are defects sparkbench actually had open, not invented prompts. Each ran in a fresh
`git worktree --detach` off `HEAD`, thrown away afterwards.

- **T1** - bare `python3 -m pytest` at the repo root aborted: it descended into the vendored
  `llama.cpp/` tree and died on `ModuleNotFoundError: No module named 'appium'`.
- **T2** - `tests/test_sparkrouter_discovery.py`, 13 assertions, written first and held
  **read-only** so the model could not edit its own specification. It specified
  `tools/sparkrouter_discovery.py`, which did not exist.
- **T3** - `tests/test_auth_sidecar.py` and `tests/test_kokoro_gateway.py` imported `fastapi` at
  module level; it is absent, so two files aborted collection of all 731 tests. Open in
  `HANDOFF.md` since 2026-08-30.

## Speed: it is not the problem

36 recorded requests, measured on the wire by `tools/aider_probe.py`.

| | min | median | max |
|---|---:|---:|---:|
| first-turn latency (cold, prompt > 500 tok) | **1.63 s** | **3.89 s** | 8.22 s |
| prefill | 697 tok/s | 870 tok/s | 1,085 tok/s |
| decode | 68 tok/s | 76 tok/s | 83 tok/s |
| whole task, start to finish | 5.7 s | 28.8 s | 34.3 s |

First-turn prompts ran **1,219 to 3,866 tokens**. Every prediction about speed held: P4
(TTFB under 10 s), P5 (first turn under 5,000 tokens) and P6 (no more than 4 requests) are all
confirmed. Four requests came back with `prompt_n == 1`, which is the prompt cache serving a
repeated prefix - the `-ub 2048`/`q8_0`/auto-slots configuration behaving as E89 said it would.

For scale: Claude Code's floor on this same box is 44,912 tokens and 136.8 s (F98, F107).
**Aider's first turn is roughly 30x smaller and 35x faster.** That is the whole reason this
workflow is worth having.

## Correctness: it is the problem

Nine task-runs across three edit formats. `pass` requires the verify command to have failed
before and passed after.

| task | `whole` (Aider's own pick) | `diff` | `diff-fenced` |
|---|---|---|---|
| T1 - create `pytest.ini` | fail | fail | fail |
| T2 - create a file from a read-only spec | **pass, 13/13** | fail, 2/13 | fail, 12/13 |
| T3 - edit two existing files | fail, 0 files touched | fail | **pass** |

**No single configuration passes more than one task.** That is the finding, and it is not a
speed problem, a context problem or a hardware problem.

### T1 - the same confidently wrong answer, four times

Every attempt wrote:

```ini
[tool:pytest]
testpaths = tests
norecursedirs = llama.cpp
```

`[tool:pytest]` is the `setup.cfg` section header. In `pytest.ini` it must be `[pytest]`, so
the file is **silently ignored** and the defect it was meant to fix survives untouched. This
reproduced 4 times out of 4 across three edit formats, including a run whose instruction said
"take care to use the section header that `pytest.ini` itself requires". Aider printed
`Applied edit to pytest.ini` and exited 0 each time.

The dangerous property is not that it was wrong. It is that the diff is three plausible lines,
the tool reported success, and only running the thing catches it.

### T3 - `whole` loses the edit and then says it did not

At `whole`, the model reproduced **31 of 72 lines (43%)** of `test_auth_sidecar.py` and stopped.
The same shape appeared three times: 25/56 (45%), 31/72 (43%), 31/72 (43%). Aider discarded the
incomplete rewrite, asked for more files, and spent a second turn replying that the changes were
"complete and correct". `files_touched` was empty.

This is not an output cap. Asked directly for a long completion with `max_tokens` unset, the
server returned 1,492 tokens with `finish_reason: "stop"` - the model stops of its own accord.
Splitting T3 into two single-file tasks did not help; the elision is per-file, not per-request.

`diff-fenced` fixed it completely: one request, 13.2 s, 383 output tokens, both files correct,
731 tests collecting, no test function lost.

### T2 - the model's best work, and its cost

At `whole` the model wrote a 137-line implementation that passed **13 of 13** assertions on the
first attempt, from a specification it could only read. That falsifies **P3**, which predicted
it would not.

The code works and would not pass review as written: **26 ruff findings** - `Tuple` and `Path`
imported and unused, three assigned-and-never-used locals, `Dict`/`Union` instead of builtin
generics despite `from __future__ import annotations`, six over-length lines. Raw output kept
verbatim at `results/raw/e90/T2-model-output-sparkrouter_discovery.py`; the cleaned version is
what shipped as `tools/sparkrouter_discovery.py`.

**Green tests are not a clean file.** Lint it before you read it.

### P8 was falsified in both halves

Amendment 2 predicted `diff` would fix T3 and cut prompt tokens. It did neither: T3 still
failed, T2 regressed from pass to 2/13, and the first-turn prompt **rose** from 1,403 to 3,621
tokens on T1, because the `diff` system prompt carries worked examples. Recorded as falsified,
not re-fitted.

## Operator friction, measured rather than recalled

- **Aider's exit code is worthless here.** It exited **0 on all nine runs**, including the four
  that changed no file at all and the four that wrote an inert `pytest.ini`. Any workflow that
  branches on it will report success indefinitely.
- **Auto-commit is on by default** and did commit - correctly, staging only the two files it
  edited, not the session's other uncommitted work. Safe on that axis, but it means a wrong
  change lands with a confident message. `tools/local-code` turns it off.
- **The repo map scans 1,882 files on every start** (~1 s) and prints nine
  `Repo-map can't include ...` warnings for `spikes/coding-screen/fixtures/`, plus a
  large-repo warning.
- Aider appends `.aider*` to `.gitignore` unasked. Wanted here; worth knowing.

## Three of my own instrument defects, recorded because they nearly became findings

Run 1 scored every task `invalid-precondition` and none of it was the model:

1. **Every verify lost its exit status through a pipe.** `pytest ... | tail -12` reports
   `tail`'s status. That is `shell-and-command-safety.md` rule 2, walked into anyway. Seed and
   verify now run under `bash -o pipefail`.
2. **A new file produced no diff.** `git diff HEAD` ignores untracked files, so T2's entire
   output was recorded as empty and then destroyed with the worktree. `git add -A -N` first.
3. **A fully-skipped module exits 5, not 0.** `pytest tests/test_x.py --collect-only` on a module
   that `importorskip` skips collects nothing and returns `EXIT_NOTESTSCOLLECTED`. This scored a
   **correct** `diff-fenced` edit as a failure. The replacement gate
   (`tools/e90/verify_t3.sh`) asserts the suite collects with no errors **and** that every
   `def test_` present at `HEAD` is still present - because "no tests collected" and "the tests
   were deleted" are otherwise the same observation.

Also: `tests/test_sparkrouter_discovery.py` was committed in its red state before the
implementation existed, contaminating T3's collection count until `--ignore` was added.

## The verdict

**Useful, with one condition: never trust the run, only the verify.**

The economics are good. A first turn costs 1.6-5 s against Claude Code's 136.8 s on the same
box, it is free, and nothing leaves the machine. On the task it is best at - writing a new file
against a precise, read-only specification - it produced correct code first try.

But it produced a plausible, confidently wrong, silently inert change on one task and reported
success; it silently dropped its edits on another and reported success. Both were caught only by
running something afterwards. So the workflow is dependable exactly to the degree that a verify
command is attached to it, which is why `tools/local-code` refuses to give a verdict without one
and exits 2 rather than pretending.

**Use it for:** a change you can name a test for; new files against a spec; small bounded edits
you will read.
**Do not use it for:** anything where you would accept "it says it worked" as the answer.

## Reproducing this

```
python3 tools/aider_probe.py --port 8499 --log /tmp/probe.jsonl &
python3 tools/aider_task_runner.py --tasks tools/aider-tasks.json \
    --workdir /tmp/e90 --probe-log /tmp/probe.jsonl \
    --model openai/$(python3 -c "import json,urllib.request as u; print(json.load(u.urlopen('http://127.0.0.1:8400/v1/models'))['data'][0]['id'])") \
    --out results/raw/e90/rerun.json
```

Raw: `run2-whole.json`, `run3-diff.json`, `run5-diff-fenced.json`, `run4-split.json`,
`t3-{whole,diff-fenced}.json`, `fmt-{udiff,diff-fenced,udiff-simple}.json`, and the model's
verbatim T2 output.
