# File: REPORT-STANDARD.md
# Purpose: The standard for who writes what in sparkbench's published reports, and the path a report takes to the site.
# Project: sparkbench | Date: 2026-11-06
#
# Overview: Codifies the July 2026 split (webby docs/plans/2026-07-12-local-ai-wordpress-migration-design.md,
# approved; sparkbench r4.0, 2026-07-14) as amended by the owner on 2026-11-06 (sparkbench may draft reader prose,
# marked DRAFT). Replaces the "Release-4.0 handoff spec" that tools/build_data_package.py used to cite: that document
# was never found in sparkbench or webby. Sections: roles, the three kinds of artefact, the path to publication, rules,
# and the history behind them.

# Report standard: who writes what

## In plain English

sparkbench measures things and writes down what it found. The owner writes what readers see. webby puts it on the
website. sparkbench may also write a first draft of the reader-facing text to save the owner time, but a draft is
always labelled as one, and only the owner's rewrite is published. Every number on the site comes from the claims file
sparkbench ships, never from the prose.

## Roles

| Who | Owns | Does not |
|---|---|---|
| **sparkbench** | Measurements, findings (`docs/FINDINGS.md`), the claims file, release notes, evidence-page entries. Also a DRAFT of reader prose, when a report is due. | Publish prose, hand a draft to webby, edit published text. |
| **Owner** | All reader-facing prose. Rewrites every draft. Decides what is published and when. | - |
| **webby** | Rendering in WordPress, wiring each claim marker to its number, checking release dates and versions match. | Reason about benchmark results, build tables from raw experiments, write evidence. |

webby consumes sparkbench's output. It does not re-derive it. Evidence questions belong in sparkbench (webby
`docs/HANDOFF-2026-09-22-sparkbench-local-ai-evidence-gaps.md`).

## Three kinds of artefact

### 1. The data package (sparkbench, final)

Built by `tools/build_data_package.py` into `dist/sparkbench-data-rX.Y/`. Contains the claims file, findings,
evidence and release notes. Every release adds a `RELEASE_HIGHLIGHTS` entry naming new findings, changed claims
(old -> new) and retractions. This is the only source of numbers for the site.

### 2. Evidence-page entries (sparkbench, final)

Forensic write-ups for the technical Evidence page, written from the sources only. Each entry has six parts, from the
owner's 2026-09-22 rewrite brief:

1. **Finding** - one or two sentences.
2. **Why we tested it**
3. **Result** - the numbers, each one a claim or a figure in the cited results file.
4. **What it means** - what the result justifies saying, and no more.
5. **Limits** - numbered.
6. **Raw evidence** - results file, raw record paths, claim IDs.

These are factual records, not buyer copy, so sparkbench's version is the final one. File them as
`reports/YYYY-MM-evidence-entries-<topic>.md`. Example: `reports/2026-11-evidence-entries-coding.md`.

### 3. Reader prose (sparkbench drafts, owner rewrites)

- The file name ends `-DRAFT.md`, for example `reports/2026-11-07-local-coding-DRAFT.md`.
- The first line under the file header is `**DRAFT FOR OWNER REWRITE - not for publication.**`
- Every number in it carries its claim ID, so the owner can see where it came from and webby can wire the marker.
- It follows the owner's voice notes (decision-maker reader, plain English, no applause lines), but it is still a
  draft. Its framing is a suggestion, not a decision.

## The path to publication

1. sparkbench runs the experiment and scores it against the pre-registration.
2. sparkbench adds findings and claims, writes evidence entries, and builds the data package release.
3. If a reader-facing report is due, sparkbench writes the `-DRAFT.md`.
4. The owner rewrites it. The rewrite is the owner's text, wherever it is kept.
5. webby renders the owner's text and the evidence entries, wired to the release's claims file.
6. webby's release-stamp check confirms the page and the claims file name the same release.

sparkbench's part ends at step 3. Nothing goes from sparkbench to webby except the data package and evidence entries.

## Rules

1. **Numbers live in claims, not prose.** When a measurement changes, update the claim and the release notes. Never
   edit published prose to change a number.
2. **A draft is never final.** Never pass a `-DRAFT.md` to webby, and never remove the DRAFT label. The owner removes
   it by rewriting.
3. **Plain English first.** Every results file, evidence file and draft opens with `## In plain English`.
4. **No tables across experiments that cannot be compared.** If a reader question needs a comparison that no single
   experiment measured, the answer is a new experiment or a stated gap, not a table assembled from unlike runs
   (webby handoff 2026-09-22: "must not become 'write the missing table'").
5. **State the limits where the claim is made.** A claim and its main limit appear together, in the evidence entry and
   in the draft.

## History

- **2026-07-12:** webby's WordPress migration design, approved by the owner. Prose "hand-edited directly in the
  WordPress block editor, matching Alastair's stated intent to personally rewrite the report text"; numbers only from
  the claims file sparkbench delivers.
- **2026-07-14:** sparkbench r4.0. Data package only, no HTML; "prose owned by editorial/webby".
- **2026-09-22:** the owner's rewrite brief for the five /local-ai/ pages, recorded verbatim in webby
  (`docs/plans/2026-09-22-local-ai-rewrite-brief.md`). It set the six-part evidence entry used above.
- **2026-09-25:** sparkbench wrote a full reader-facing report (`reports/2026-09-25-vendor-claims-on-your-own-box.md`)
  and a one-pager, outside the July split. Under this standard it counts as a draft for the owner to rewrite, not as
  published prose.
- **2026-11-06:** owner decision: sparkbench may draft reader prose, marked DRAFT; the owner rewrites; webby renders.
  This document records it.
