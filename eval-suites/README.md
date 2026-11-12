# eval-suites/

Every file in this folder with its own one-line description (a document's title, or a script's Purpose line). A blank means the file does not state one.

| File | Description |
|---|---|
| [audit_ceiling.py](audit_ceiling.py) | Report, for every stored eval answer, whether it finished or was cut off - and by which ceiling. |
| [compare_methods.py](compare_methods.py) | Measure how often keyed scoring and blind pairwise judging disagree on the same answers. |
| [delivery.py](delivery.py) | Decide what actually stopped a generation - the context window, the output ceiling, or the model itself - from the server's own log rather than from a text heuristic. |
| [e10-generation.yaml](e10-generation.yaml) | E10 - long structured generation: complete model/tg128 table from the 12K log. |
| [e8-32k.yaml](e8-32k.yaml) | E8 - 32K-context eval with cross-chunk reference questions (Scout chunked-attention quality fork). |
| [e9-contradiction.yaml](e9-contradiction.yaml) | E9 - adversarial contradiction detection over the 12K log with a planted erratum. |
| [hardlong.yaml](hardlong.yaml) | Eval v2 hard long-context suite (E7) - multi-hop, arithmetic, and cross-reference tasks over the 12K-token log excerpt. |
| [judge_pairwise.py](judge_pairwise.py) | Run the Material-Outcome Test rubric as a blind pairwise judge over stored answers. |
| [models-upper-limits.txt](models-upper-limits.txt) |  |
| [models.txt](models.txt) |  |
| [promptfooconfig.yaml](promptfooconfig.yaml) | Eval-pilot suite - 4 task types x short/long context, deterministic assertions (spec: docs/plans/2026-07-04-eval-pilot.md). |
| [score_keyed.py](score_keyed.py) | Score a model answer against a ground-truth key, so a single answer can be measured without an opponent. |

**Folders:** [data/](data/) · [keys/](keys/) · [rubrics/](rubrics/)
