# File: memory-edge-deadlock.md
# Purpose: Canonical, self-contained reference for the amdgpu SDMA-suballocator
#          deadlock that near-edge model loads hit on sparkmax under memory
#          pressure - its fingerprint, mechanism, triggers, recovery, and the
#          rules that prevent it.
# Project: sparkbench | Date: 2026-07-13
#
# Overview: sparkmax (Ryzen AI Max+ 395, 128 GB unified RAM, Radeon 8060S / RADV)
# has a hardware/driver failure mode where loading a large model can wedge the
# machine in an unkillable kernel deadlock that only a PHYSICAL POWER CYCLE
# clears. It is the single most operationally serious finding in the project
# because it cannot be recovered remotely and agent-spark (non-sudoer) cannot
# even reboot the box. This document consolidates findings F24, F25, F26, F27,
# F28 and the C1 live reproduction into one place: what the failure looks like,
# what actually causes it, when it does and does NOT happen, and exactly how to
# recover. Read this before any large-model (>~60 GiB weights) session.

## STATUS 2026-08-29: the SIZE trigger is retracted, the contention trigger did not reproduce

E89 (F109) ran a five-rung ladder to **105.15 GiB absolute GTT**, all rungs served,
zero `drm_suballoc_new`. It then reproduced F24's contention shape deliberately - a
121.6 GiB `sha256sum` loop held against the largest rung at **0 GiB free with swap
engaged** - and that loaded in 32.3 s and served 10 of 10 requests.

F24 and C1 were recorded on kernel **6.17.0-35**; this box now runs **7.0.0-29**
and amdgpu is in-kernel, so a kernel fix is the leading explanation. That is a
HYPOTHESIS - booting 6.17 to test it was not done. **F27's cumulative-state case
(82 GiB, no I/O identified, after ~13 load cycles) remains untested**; the E89
ladder ran 5 cycles.

Everything below this line remains an accurate account of what was observed in
July 2026 on kernel 6.17.0-35. Read it as history plus a fingerprint to watch for
after any kernel change, not as a live size limit.

## TL;DR

Loading a near-edge model (weights >~60 GiB) **while the machine is under memory
pressure** can deadlock the amdgpu driver's small-buffer suballocator during the
GPU's VM page-table setup. The stuck process is **uninterruptible (D-state)**,
`SIGKILL` does nothing, it never self-resolves, and a graceful `sudo reboot`
**stalls on it** - clearing it requires a **hard power cycle** by someone
physically at the machine. The trigger is memory pressure crossing the 128 GB
RAM ceiling, most easily caused by heavy disk I/O (downloads, hashing, backups)
running concurrently with the load. Big models are **safe for inference** when
nothing else is competing for RAM/disk (proven: a 103 GB model drafted the full
task set cleanly on 2026-07-13). The rule is not "don't run big models" - it is
"don't run big models under memory contention, and be present to power-cycle."

## The fingerprint - how to know it is THIS and not something else

All five observed occurrences share one signature. If you see these together,
it is this deadlock, not a normal OOM abort and not disk thrash:

| Signal | How to read it (non-sudoer OK) | Deadlock value |
|---|---|---|
| **wchan** | `cat /proc/<pid>/wchan` | exactly `drm_suballoc_new` |
| **Process state** | `grep State /proc/<pid>/status` | `D (disk sleep)` - uninterruptible |
| **VRAM used** | amdgpu `mem_info_vram_used` sysfs | parks at **exactly 2.00 GiB** (2,147,483,648 B), held steady, never climbs toward the model's real footprint |
| **Resident set** | `grep VmRSS /proc/<pid>/status` | flat / collapsed (~30-57 MB) - the load never finishes becoming resident |
| **read_bytes** | `/proc/<pid>/io` | climbs *past* the model size (retry/thrash) then flatlines |
| **vmstat** | `vmstat 1` | si/so/bi/bo near-zero *after* the stall - it is deadlocked, not swapping |
| **Killability** | `kill -9 <pid>` | no effect - SIGKILL cannot act on a D-state task in this path |
| **Self-resolution** | wait and re-check wchan | none - unchanged after 24-44+ minutes |

The **2.00 GiB VRAM park + `drm_suballoc_new` wchan** pair is the tightest tell:
the backend got its first buffer (2 GiB) and then starved waiting for the rest.

Full kernel stack (the ONE `dmesg`-confirmed instance, F24, needs sudo/Alastair):
```
amdgpu_cs_ioctl -> amdgpu_vm_bo_update -> amdgpu_vm_sdma_prepare ->
amdgpu_job_alloc_with_ib -> amdgpu_sa_bo_new -> drm_suballoc_new -> schedule
```
A wait on the driver's own small-buffer suballocator for VM page-table-update
SDMA jobs - not a Vulkan heap-reporting limit, not a clean DeviceLost/SIGABRT.

## Mechanism - what is actually happening

Established by the C1 positive-control reproduction (2026-07-10, watched live;
docs/plans/2026-07-10-deadlock-cause-isolation.md):

The operative trigger is **memory pressure, not disk I/O per se.** Once the
model (e.g. 68 GiB) plus the concurrent I/O's file-cache reads exceed 128 GB
RAM, model pages get evicted and re-read (observed: RSS dropped 64->53 GiB while
`read_bytes` climbed past the model size). The GPU backend gets its first buffer
but cannot get the rest resident; the VM-update SDMA suballocator starves
waiting for a small buffer that can never be satisfied, and the whole path
deadlocks. Confirmed a **true deadlock, not thrash**: removing all I/O pressure
did not recover it, and `SIGKILL -9` left the process present and still D-state.

Disk I/O (hashing/downloads/backups) is the usual *cause* of the memory pressure
because those reads compete with the model for the page cache - but it is the
memory ceiling crossing that is doing the damage, which is why the rule is about
contention, not about disk activity in the abstract.

## Triggers - confirmed vs candidate

**CONFIRMED (F24 + C1 live repro):** a near-edge weight load (>~60 GiB) under
memory pressure from concurrent heavy disk I/O that pushes total RAM usage over
128 GB. Original instance: a 62 GB `sha256sum` running alongside GLM-4.5-Air's
~68 GiB Vulkan load.

**CANDIDATE, unconfirmed (F27):** *cumulative driver/GPU-state degradation*
across many large-model load/unload cycles in one session without a reboot. F27
deadlocked on the model with the MOST headroom in its batch (Devstral 2 123B,
29.81 GiB clear of the ceiling) with **no** heavy concurrent I/O identified,
after ~13 large-model load cycles that session. Not established - the wchan
matched F24 but the full `dmesg` trace could not be re-captured (sudo-restricted,
and the ring buffer did not survive the power cycle). Flagged, not asserted.

**CANDIDATE, unconfirmed (F27):** a *lighter-weight I/O trigger* than the
original 62 GB hash - modest filesystem activity (file copies, stderr redirects)
in quick succession may suffice under the right timing.

**CANDIDATE, unconfirmed (F28):** an *immediate retry of a leg that just crashed
with a clean DeviceLost* may itself elevate risk, as if the crashed attempt
leaves GPU/driver state partly unwound so the very next load is more fragile -
even though an intervening idle check showed VRAM back at baseline. n=1, no
controlled comparison. Falsifiable test for a future session: does a longer
cooldown before a post-crash retry reduce recurrence?

## When it does NOT happen (the negative controls)

Equally important - these are why the rule is "avoid contention," not "avoid big
models":

- **Idle near-edge load, no concurrent I/O:** passes clean. GLM-4.5-Air's exact
  ~68 GiB invocation ran cleanly with no I/O (F24 same-session re-run; F26
  re-ran it clean at BOTH ttm pool ceilings). Vulkan was never observed to abort
  under any *controlled idle* condition in the whole F24-F26 investigation.
- **Big-model DRAFTING, box otherwise quiet (2026-07-13, attended):**
  command-a-plus (**103 GB** weights) ran the full 10-task drafting set with
  **D-state 0 throughout**; GLM-4.5-Air (73 GB) likewise. Load ~85 s, gen
  ~2 min/task. Inference is low-I/O and put the box under no memory pressure, so
  even 103 GB - well past the ~60 GiB edge - was safe. This is the operational
  green light: **a big model is safe to serve when nothing else is hammering
  RAM/disk and you are present to power-cycle if the *load* stalls.**

The distinction that matters: **raw weight size is not the trigger; weight size
PLUS memory contention is.** A 103 GB model idle-loads fine; a 68 GB model under
a hashing loop deadlocks.

## Recovery - requires a HARD POWER CYCLE

1. **It is unkillable.** `SIGKILL` cannot act on a D-state task in this kernel
   path - confirmed ineffective across all three deadlock occurrences.
2. **It does not self-resolve.** Unchanged after 44+ minutes; do not wait it out.
3. **A graceful `sudo reboot` STALLS on the wedged task.** The box goes to "No
   route to host" and never comes back on the clean path. Confirmed on TWO
   consecutive occurrences (F27 2026-07-09, F28 2026-07-10) - it is no longer a
   one-off. A **hard power cycle** (physical button, someone at the machine) is
   required both times.
4. **agent-spark is a non-sudoer** and cannot reboot at all - recovery needs
   Alastair physically present. Budget for this before any attended big-model run.
5. **Capture evidence BEFORE the power cycle.** The `dmesg` ring buffer does NOT
   survive a power cycle, so the full kernel trace is lost on reset. As a
   non-sudoer, snapshot what you can the moment a load stalls: `wchan`, `status`
   (State + VmRSS), `io` (read_bytes), and the amdgpu VRAM figure. The wchan
   match is the only evidence that survives - it is the permanent record.

**Post-recovery sign-off checklist** (do not trust the box until all pass):
- no stray `llama-server` / `llama-bench` processes (`pgrep -x`),
- no D-state tasks (`ps -eo stat,comm | awk '$1 ~ /D/'`),
- **pause `llama-gateway.service`** - it auto-restarts on boot and holds the 30B
  on the GPU, violating the one-model-at-a-time rule before the sanity bench,
- a known-good small-model sanity bench (Qwen3-4B) loads and infers at nominal
  baseline speed.

## Operational rules (prevention)

1. **Never run heavy disk I/O concurrently with a near-edge load.** No downloads,
   `sha256sum`, or backups while a >~60 GiB model is loading. (F24)
2. **Keep weights + concurrent file cache well under 128 GB.** The real trigger
   is memory pressure crossing the RAM ceiling, not disk activity in itself. (C1)
3. **One model at a time.** Pause the gateway
   (`systemctl --user stop llama-gateway.service`) before any big-model load; it
   otherwise holds the 30B resident.
4. **Always bound the KV cache: `-c 8192`** (or another explicit value). `-c 0`
   over-allocates on a 262K-context model and eats the headroom.
5. **Be present to power-cycle for any load >~60 GiB.** Attended only. Have
   Alastair ready before starting.
6. **Do not immediately retry a leg that just DeviceLost** - cool down or reboot
   first (F28 candidate trigger; cheap precaution).
7. **Consider bounding load/unload cycles per session** without a reboot during
   heavy campaigns (F27 candidate trigger - cumulative state; not established,
   but prudent).
8. **Snapshot wchan/status/vram the instant a load stalls,** then request the
   hard power cycle (the `dmesg` trace will not survive it).

## Instrumentation (non-sudoer, ready to paste)

```bash
# Is anything wedged right now? (the dstate() check used by big_model_test.py)
ps -eo stat,comm | awk '$1 ~ /D/ && $2 !~ /jbd2|kworker/'

# The definitive tell for a suspect PID:
cat /proc/<pid>/wchan                       # -> drm_suballoc_new  == this deadlock
grep -E 'State|VmRSS' /proc/<pid>/status    # -> D (disk sleep), flat VmRSS
cat /proc/<pid>/io | grep read_bytes        # -> climbs past model size then flatlines
```
`dmesg` (the full kernel stack) needs sudo - request it from Alastair while the
task is still wedged, before the power cycle wipes the ring buffer.

## Evidence trail

| Ref | Date | Model / size | Trigger present | Confirmation |
|---|---|---|---|---|
| **F24** | 2026-07-08 | GLM-4.5-Air ~68 GiB | 62 GB concurrent `sha256sum` | full `dmesg` kernel trace (the decisive one) |
| **C1** | 2026-07-10 | GLM-4.5-Air ~68 GiB | deliberate infinite hash loop | live-watched repro; proved memory-pressure mechanism |
| **F27** | 2026-07-09 | Devstral 2 123B, 82 GiB (most headroom) | none identified | wchan match; hard power cycle to recover |
| **F28** | 2026-07-10 | Command A+ Q3, 95.5 GiB | immediate retry after DeviceLost | wchan match; hard power cycle to recover |
| (neg) | 2026-07-08 | GLM-4.5-Air ~68 GiB idle | none | passes clean at both ttm ceilings (F26) |
| (neg) | 2026-07-13 | command-a-plus 103 GB drafting | none (quiet box) | full task set, D-state 0 throughout |

F25/F26 are part of the same investigation: F25 originally claimed "ROCm
succeeds where Vulkan aborts," F26 **retracted** it as confounded by a
concurrent GRUB/ttm-ceiling change - Vulkan never actually aborted under any
controlled idle condition, and F6's original DeviceLost remains unreproduced.
The deadlock documented here (F24 class) is unaffected by that retraction; it
stands on its own kernel-trace evidence.

Source records: docs/FINDINGS.md F24-F28; docs/PHASE-A-LOG.md 2026-07-08/09/10
entries; docs/plans/2026-07-08-vulkan-memory-ceiling-investigation.md;
docs/plans/2026-07-10-deadlock-cause-isolation.md (C1);
docs/plans/2026-07-09-repeatability-campaign-plan.md (F28); results/experiments.md
E22/E23; tools/big_model_test.py (the `dstate()` health-watch encodes rule 8).

## Open questions (unresolved, flagged per discrepancy discipline)

- **Is concurrent heavy I/O necessary, or only sufficient?** F27 deadlocked with
  no identified heavy I/O and the most headroom in its batch. If the trigger can
  be cumulative session state, the operational bound is broader than "avoid
  concurrent I/O" - possibly a cap on load/unload cycles per session.
- **Does immediate-retry-after-DeviceLost genuinely elevate risk?** (F28, n=1.)
  Testable: vary the cooldown before a post-crash retry.
- **F6's original DeviceLost trigger remains unreproduced** (distinct failure
  class from this deadlock; see F26). Not the same bug - do not conflate them.
