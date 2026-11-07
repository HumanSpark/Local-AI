# E36 PRE-REGISTRATION: single-model concurrency UNDER THE ROUTER (2026-07-17)

# File: results/router-concurrency-prereg.md
# Purpose: Predictions registered BEFORE the E36 runs - does the router change F17's concurrency knee?
# Project: sparkbench | Date: 2026-07-17
#
# Overview: F41 measured concurrency ACROSS two models (bandwidth-bound, 4.6:1 unfair). This is the
# other axis and the last item F40/F41 left open: many concurrent requests to ONE model, served through
# the router instead of directly. F17 measured this on a direct llama-server: workhorse 72.9 -> 193.5
# t/s aggregate from 1 to 16 slots (2.66x, no sharp knee). The question is whether the router's proxy
# hop changes that. Results land in results/router-concurrency.md.

## The methodological point that shapes the design

**F17's numbers cannot be the baseline.** F17 was measured on an older llama.cpp build; this box now
runs v200 (067de93). Comparing router-now against F17-then would confound the router's effect with
every build change in between - exactly the class of error that produced this week's `--jinja`
retraction (a config difference asserted without running both configs).

So both arms are measured in THIS session, on THIS build, with ONE driver:
- **DIRECT arm:** plain `llama-server -np N -c N*4096`, native `/completion`.
- **ROUTER arm:** router mode, same `-np N -c N*4096` inherited by the model instance, same
  `/completion`, plus the `"model"` field the router requires.

The driver replicates serve_bench.py's semantics exactly (one thread per slot; discarded warmup;
barrier-synced start; 45s measured window; `n_predict=128`, `temperature=0`, `cache_prompt=false`;
unique `[req tid-n]` prompt prefix to defeat prompt caching; aggregate = sum(predicted_n)/wall from
server-side timings). serve_bench.py itself cannot be reused: it launches its own server, so it cannot
drive an already-running router - and using serve_bench for one arm and a new driver for the other
would be two rulers. One driver, both arms.

Feasibility already probed (not a measurement): native `/completion` through the router returns **400
Bad Request without a `"model"` field** and works with one. A direct llama-server needs no such field.
That is recorded as a migration caveat regardless of how the numbers land.

## Predictions

Sweep N = 1, 4, 16 slots, both arms.

- **P1. The DIRECT arm reproduces F17's shape on the new build:** ~70-75 t/s at 1 slot rising to
  ~180-200 t/s at 16, i.e. a ~2.4-2.9x scaling ratio with no sharp knee. *If this misses, it is a
  BUILD finding, not a router finding* - and it would mean F17's banked numbers no longer describe
  this stack, which matters more than the router question.
- **P2. The router costs ~nothing at 1 slot:** router aggregate >= 0.95 x direct. One proxied request
  at a time should be a memcpy and a socket, not a bottleneck.
- **P3. The router costs ~nothing at 16 slots either:** router/direct >= 0.90 at every N, and the
  scaling RATIO (16-slot / 1-slot) is within 0.2x of direct's. *Confidence: moderate.* The router
  proxies every request through an extra HTTP hop; at 16 concurrent streams that is 16 proxied
  connections, and if the proxy serialises or copies aggressively it would throttle. **If P3 misses,
  the router is unsuitable for multi-client serving** and that is the decision-grade result.
- **P4. TTFT gains a small constant under the router:** p50 higher by < 50ms at 1 slot, and the ~6x
  growth from 1 to 16 slots that F17 recorded is preserved in shape.
- **P5. No deadlock, D-state 0.** 16 slots x 4096 = 64K total context on an 18.6 GB model is ~21 GiB -
  nowhere near the ~60 GiB edge (F24).

## Decision rule

- P3 HIT -> the router is viable for concurrent serving as well as switching; the only remaining
  objection is llama.cpp's own "experimental" label.
- P3 MISS -> the router is a single-operator convenience only. Any LAN multi-client use keeps the
  current direct-serving gateway, and F40's "adopt the router" option narrows to switching.
- P1 MISS -> stop and report: F17's concurrency numbers would be stale for this build, which is a
  bigger finding than E36 and would need its own re-measurement before anything is concluded here.

## Safety

Gateway paused (rule 3), KV bounded explicitly at 4096/slot (rule 4), preset-only never `--models-dir`
(F40), disk quiet (rule 1), attended, D-state polled every arm. Peak ~21 GiB, far under the edge.
