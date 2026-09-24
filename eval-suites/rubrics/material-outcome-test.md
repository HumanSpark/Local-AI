# File: material-outcome-test.md
# Purpose: Third-party LLM-judge rubric that scores answers by what materially changes for the
#          client, not by polish, length or apparent sophistication.
# Project: sparkbench | Date: 2026-08-11
#
# Overview: Verbatim copy of the judge prompt used by the CloseVector Legal Reasoning Benchmark,
# adopted under its own explicit reuse invitation (quoted below). Body text below the provenance
# block is UNMODIFIED - do not edit it in place. If we change the rubric, copy it to a new file so
# the disagreement between our variant and the original stays measurable.

## Provenance

| Field | Value |
|---|---|
| Source URL | https://legal-benchmarks.netlify.app/ (`evidence/series-1/eval_prompt.txt`, `evidence/series-2/eval_prompt.txt`) |
| Release | `CV-LRB-2026.08.10-R9`, dated 2026-08-10 |
| SHA-256 | `7e58b951cb86e4deba3b60fd01e9b9bd247ebe9883e1c9e43b24acffb1fd4667` |
| Size | 7,976 bytes |
| Verified | 2026-08-11 - recomputed from both mirrored series independently; both match the published value and each other |
| Reuse basis | *"An example evaluation prompt. A starting point, not scripture. Steal it, break it, improve it."* - the file's own header |

**Licence scope.** The publication as a whole carries **no licence**, so default all-rights-reserved
applies to it. The invitation quoted above is carried by this file specifically and is the basis for
this copy. It does **not** extend to the 80 legal matters or their answer keys - those are not
reproduced here and must not be. Review: `reports/2026-08-11-closevector-legal-benchmark-review.md`.

**Why we took it.** It bans the vocabulary that makes most LLM-judge output worthless ("could create
risk", "might affect strategy"), has no "slightly better" category, and requires a seven-element
proof before any winner is declared. Measured on that publication's own 240 verdicts, the longer
answer won only 55% of decisive verdicts - 38% once three truncated answers are excluded - while the
verbose arm wrote the longer answer in 75 of 80 matters. The length ban held in practice.

It is explicitly domain-general (*"substituting the equivalent consequences for the domain at
hand"*), so it applies unchanged to non-legal eval-pilot material.

---

The Material-Outcome Test
An example evaluation prompt. A starting point, not scripture. Steal it, break it, improve it.

How to Use It
Give the judge model this prompt plus three documents: the original question, Answer A, and Answer B. Randomize which answer gets the A label across runs so position bias cannot pick your winner. Do not tell the judge which system produced which answer.

The Only Question
What concrete, material thing happens differently to the client because the decision-maker received one answer rather than the other?

"Client" means whoever bears the consequences of the decision — a client, patient, customer, employer, or the decision-maker themselves.

Length, detail, sophistication, citation density, formatting, confidence, and apparent intelligence carry zero weight unless they materially improve the client's actual position.

If both answers put the decision-maker on the same materially correct and safe path to the same materially safe result, the verdict is: TIE, FUNCTIONALLY EQUIVALENT.

There is no "slightly better" category.

What Counts as Material
A difference counts only if it would cause a competent professional to decide or act differently, AND that change concretely alters the client's legal, financial, medical, technical, evidentiary, procedural, safety, or operational position.

Examples, substituting the equivalent consequences for the domain at hand: a claim preserved versus lost, a deadline or filing met versus missed, privilege or confidentiality protected versus waived, a correct versus incorrect diagnosis or treatment, a design that passes versus fails inspection, a transaction priced or authorized materially differently for a supported reason.

Not material by itself: different reasoning that produces the same correct action, a spotted issue that changes no decision, an omitted issue unnecessary to the correct result, or confidence language that changes no conduct.

Banned as substitutes for proof: "could create risk," "might affect strategy," "less complete," "raises concerns," and their cousins, unless immediately followed by a specific different action and a concrete, record-supported consequence.

The Two-Client Test
Professional A receives only Answer A. Professional B receives only Answer B. Both exercise ordinary judgment and ordinary verification in their field. Neither blindly follows nonsense. Neither reconstructs an analysis the answer failed to provide.

For each thing a competent professional must get right:

What would each one conclude or do?
Would they do anything materially different?
What concrete event happens differently to the client?
But for the difference between the answers, what materially different thing does the client experience? If the answer is "nothing demonstrated," the answers are functionally equivalent.

Neutralization Test
Do not simply delete disputed content and pretend it was never received.

Ask:

Would ordinary verification cause a competent reader to reject the disputed content before acting? Content is visibly unsupported when the record contains none of the inputs required to produce it.
After rejecting it, does the reader occupy the same materially safe position as the reader of the other answer?
Rejecting visibly unsupported content is ordinary reading, not corrective work. Corrective work means building the analysis the answer should have supplied.

If the content is safely rejected and the reader lands where the other answer's reader already stood, it is neutralized — stop, tie on this point.

If neutralizing it requires reconstructing omitted analysis, re-deriving a conclusion or value the answer stated confidently, or accepting material residual risk, it is not safely neutralized.

Log each neutralized point in one line, per the Output Format below.

After evaluating disputed points individually, ask once: taken together, do the neutralized points leave either reader unable to act safely? If so, run the combined effect through the seven elements as a single omission.

The Seven-Element Proof
To declare one answer materially better, prove all seven. Any element unproven, the difference is not material.

Exact difference. Quote the error or name the precise omission.
Different conduct. Exactly what Professional A does and exactly what Professional B does differently. "Better informed" is not conduct.
Concrete consequence. Identify the specific harm — the claim, deadline, protection, diagnosis, safety margin, sum, or comparable interest that is lost, missed, waived, or degraded. "Different" is not automatically "worse." Name who is harmed and in which direction. If the record cannot establish the direction of harm, this element fails.
Record support. Identify the supplied facts or rules that make the consequence foreseeable. No imagined facts.
Material magnitude. Explain why it matters to the client rather than only technically.
Likelihood. Explain why a rational professional would change conduct now, not merely in a hypothetical other case.
No safe neutralization by ordinary verification. Ordinary verification means checking cited rules, dates, calculations, and stated facts against the record. It does not include reconstructing analysis the answer omitted or re-deriving a conclusion or value the answer stated confidently. If neutralizing the difference requires the reader to do the answer's job, the difference stands.

Tie Rules
Same material conclusions, same material actions: tie.

Different reasoning, same correct action: tie.

A bare conclusion is judged as an omission. If the reader cannot safely act without the missing analysis, run the omission through the seven elements. If no analysis was needed to act, a bare conclusion ties with a dressed-up one.

Polish, length, and issue counts win nothing unless conduct or outcome changes.

Never force a tie over a proven divergence. Never manufacture a divergence to avoid a tie.

Both answers reaching the same materially wrong or unsafe destination means: BOTH MATERIALLY INADEQUATE.

The Final Hard Stop
Before declaring a winner, complete this sentence:

"Because Answer [A or B] said or omitted ______, the reader would likely do ______ instead of ______, causing the client to experience ______."
If it cannot be completed with a concrete, record-supported consequence, the answers tie.

Verdict options, exactly one:

TIE, FUNCTIONALLY EQUIVALENT.
ANSWER A IS MATERIALLY BETTER.
ANSWER B IS MATERIALLY BETTER.
BOTH MATERIALLY INADEQUATE.
Output Format
Report in this order and nothing else:

Verdict. One of the four verdicts, first line, standing alone.
Basis. Two to four sentences. For a tie: the shared material path both readers end up on, stated once. For a winner: the single proven divergence. For BOTH MATERIALLY INADEQUATE: the shared defect and the concrete risk it leaves with the client. Do not walk through the answers issue by issue.
Proof (winner verdicts only). The seven elements, one line each. Omit for any other verdict.
Neutralization log. One line per rejected point, format: [A/B] rejected: [content] — [record lacks X / record contradicts Y / cited authority says otherwise / internally inconsistent with Z]. No headers, no paragraphs, no per-point explanation of why the reader is still safe — that is stated once in the Basis, not repeated per line. Omit the log if nothing was rejected.
Failed candidates. One line per candidate divergence: name it and name the first element that failed. This must cover every candidate divergence surfaced by the Two-Client Test, not a selection.
Hard stop. The completed sentence, or the single statement that it cannot be completed.
The entire report should fit on one screen. Verbosity is not rigor. The log is an audit trail, not a critique and not a defense — do not editorialize about either answer's quality, discipline, or style, do not characterize errors beyond the log line, and do not restate points of agreement between the answers.
