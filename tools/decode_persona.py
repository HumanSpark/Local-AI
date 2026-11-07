# File: tools/decode_persona.py
# Purpose: Decode nibble-packed personas from the MatrAIx Persona 1M release into
#          readable attribute maps, and print them for inspection.
# Project: sparkbench | Date: 2026-09-03
#
# Overview:
#   The release stores each persona's 1,290 attributes as 645 bytes of 4-bit codes
#   (low nibble first) indexed against persona_codes.schema.json. The `datasets`
#   library cannot read these files at all; pyarrow plus this decoder can.
#
#   Decode rules, all three of which the upstream card calls out as easy to get wrong:
#     - null_bitmap: a SET bit means the attribute is MISSING, LSB first. A null
#       bitmap means nothing is missing in that row.
#     - attribute_overrides beats the decoded code: it carries exact values that
#       fall outside the codebook.
#     - rows are sparse (656 of 1,290 populated on average). Absent means the source
#       did not support the attribute; nothing is imputed. Callers branch on absence.
#
#   Flow: load_codebook() -> iter_rows() -> decode_row() -> render().
#   Row ids are global across the 10 shards; locate_row() maps one to (shard, offset)
#   using indexes/manifest.json.

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

import pyarrow.parquet as pq

DEFAULT_ROOT = Path("/opt/models/staging/matraix-persona-1m")


@dataclass
class Persona:
    """One decoded persona. `attributes` omits everything the source did not support."""

    row_id: int
    source: str
    source_record_id: str | None
    attributes: dict[str, str] = field(default_factory=dict)
    overrides: dict[str, str] = field(default_factory=dict)
    descriptions: dict[str, str] = field(default_factory=dict)
    grounding: dict[str, dict[str, Any]] = field(default_factory=dict)
    populated_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def evidence_attribution_ok(self) -> bool:
        """Whether this row's descriptions/grounding can be trusted to name their field.

        The release ships no documented index space for `descriptions[].field_index` /
        `grounding[].field_index`, and the upstream decoder never resolves them. Where
        the index set matches the row's populated attributes exactly, spot checks show
        the attribution is correct (seniority 'Student / intern' evidenced by "toss it
        in my school bag"). Where it does not, attributions are demonstrably wrong.

        Measured 2026-09-03 over 3,600 sampled rows: stackoverflow and gss 100%,
        amazon 54.5%, wiki 5.5%. Attributes are unaffected either way - only the
        evidence layer is in question. False here means use the attributes and drop
        the evidence for this row; it does NOT mean the persona is bad.
        """
        if not self.grounding:
            return False
        return sorted(self.grounding) == sorted(self._populated_indices)

    _populated_indices: list[int] = field(default_factory=list, repr=False)


class Codebook:
    """The 1,290-field schema: field ids, labels, categories and value lists."""

    def __init__(self, path: Path) -> None:
        raw = json.loads(path.read_text())
        if raw["packing"] != "nibble":
            raise ValueError(
                f"{path} declares packing {raw['packing']!r}, this decoder only handles 'nibble'. "
                f"hint: the release format changed; re-read the dataset card before decoding."
            )
        self.row_bytes: int = raw["row_bytes"]
        self.columns: list[dict[str, Any]] = raw["columns"]
        self.by_index = {i: c for i, c in enumerate(self.columns)}
        self.field_count = len(self.columns)

    def label(self, field_index: int) -> str:
        col = self.by_index.get(field_index)
        return col["label"] if col else f"<field {field_index}>"

    def field_id(self, field_index: int) -> str:
        col = self.by_index.get(field_index)
        return col["id"] if col else f"field_{field_index}"

    def category(self, field_id: str) -> str:
        for col in self.columns:
            if col["id"] == field_id:
                return col.get("category", "Uncategorised")
        return "Uncategorised"


def decode_attributes(packed: bytes, null_bitmap: bytes | None, book: Codebook) -> dict[str, str]:
    """Unpack 645 bytes of 4-bit codes into {field_id: value}, skipping missing fields."""
    if len(packed) != book.row_bytes:
        raise ValueError(
            f"packed row is {len(packed)}B, codebook declares {book.row_bytes}B. "
            f"hint: shard and codebook are from different revisions - refetch both at one sha."
        )
    out: dict[str, str] = {}
    for i, col in enumerate(book.columns):
        if null_bitmap is not None and (null_bitmap[i // 8] >> (i % 8)) & 1:
            continue  # set bit = the source did not support this attribute
        byte = packed[i // 2]
        code = (byte & 0x0F) if i % 2 == 0 else (byte >> 4)
        values = col["values"]
        if code < len(values):
            out[col["id"]] = values[code]
    return out


def decode_row(row: dict[str, Any], row_id: int, book: Codebook) -> Persona:
    """Turn one pyarrow row dict into a Persona, applying overrides over decoded codes."""
    attrs = decode_attributes(row["attributes"], row["null_bitmap"], book)

    overrides: dict[str, str] = {}
    for item in row.get("attribute_overrides") or []:
        fid = book.field_id(item["field_index"])
        overrides[fid] = item["value"]
        attrs[fid] = item["value"]  # exact value outside the codebook wins

    # descriptions/grounding are keyed by RAW field_index, never by a resolved field id.
    # Their index space is not the codebook's: indices up to 1324 occur against a
    # 1,290-column codebook, and 43% of entries point at a field the persona does not
    # have. Mapping them through the codebook produces confident nonsense (a language
    # field carrying homeownership evidence), so this decoder refuses to guess and
    # hands back the index plus whether it is even in range. Measured 2026-09-03 over
    # 12k sampled grounded rows: 43.2% of entries unmappable, max index 1324.
    populated = {
        i
        for i in range(book.field_count)
        if row["null_bitmap"] is None or not (row["null_bitmap"][i // 8] >> (i % 8)) & 1
    }
    descriptions = {
        d["field_index"]: d["text"] for d in (row.get("descriptions") or [])
    }
    grounding = {
        g["field_index"]: {
            "evidence": g.get("evidence"),
            "confidence": g.get("confidence"),
            "assignment_type": g.get("assignment_type"),
            "index_in_range": g["field_index"] < book.field_count,
            "index_is_populated": g["field_index"] in populated,
        }
        for g in (row.get("grounding") or [])
    }

    meta_raw = row.get("metadata_json")
    metadata = json.loads(meta_raw) if meta_raw else {}

    return Persona(
        row_id=row_id,
        source=row["source"],
        source_record_id=row.get("source_record_id"),
        attributes=attrs,
        overrides=overrides,
        descriptions=descriptions,
        grounding=grounding,
        populated_count=row["populated_attribute_count"],
        metadata=metadata,
        _populated_indices=sorted(populated),
    )


def shard_table(root: Path) -> list[dict[str, Any]]:
    """Shard offsets from indexes/manifest.json, so a global row id can be located."""
    return json.loads((root / "indexes/manifest.json").read_text())["shards"]


def iter_rows(
    root: Path, book: Codebook, shards: list[dict[str, Any]], want_source: str | None, limit: int
) -> Iterator[Persona]:
    """Walk shards in order, yielding decoded personas matching `want_source`."""
    seen = 0
    for shard in shards:
        path = root / shard["path"]
        if not path.exists():
            raise FileNotFoundError(
                f"shard {path} is missing. "
                f"hint: the release is 10 shards; refetch with tools/fetch_hf_dataset.py."
            )
        pf = pq.ParquetFile(path)
        offset = shard["rowStart"]
        local = 0
        for batch in pf.iter_batches(batch_size=2048):
            rows = batch.to_pylist()
            for row in rows:
                if want_source is None or row["source"] == want_source:
                    yield decode_row(row, offset + local, book)
                    seen += 1
                    if seen >= limit:
                        return
                local += 1


def render(p: Persona, book: Codebook, max_attrs: int, show_evidence: bool) -> str:
    """Format one persona for a terminal: header, grouped attributes, then text."""
    lines: list[str] = []
    rid = p.source_record_id or "-"
    lines.append(f"{'=' * 78}")
    lines.append(f"row {p.row_id}  source={p.source}  record={rid}")
    lines.append(
        f"{p.populated_count} of {book.field_count} attributes populated"
        f"{f'  ({len(p.overrides)} overrides)' if p.overrides else ''}"
    )
    lines.append("=" * 78)

    grouped: dict[str, list[tuple[str, str]]] = {}
    for fid, val in p.attributes.items():
        grouped.setdefault(book.category(fid), []).append((fid, val))

    shown = 0
    for category in sorted(grouped):
        if shown >= max_attrs:
            break
        items = sorted(grouped[category])
        lines.append(f"\n-- {category} ({len(items)})")
        for fid, val in items:
            if shown >= max_attrs:
                lines.append(f"   ... {len(items) - (shown - sum(len(v) for k, v in grouped.items() if k < category))} more in this category")
                break
            mark = "*" if fid in p.overrides else " "
            lines.append(f"  {mark} {fid:<38} {val}")
            shown += 1

    remaining = len(p.attributes) - shown
    if remaining > 0:
        lines.append(f"\n   [{remaining} further attributes not shown - raise --max-attrs]")

    if p.descriptions:
        lines.append(
            f"\n-- Field descriptions ({len(p.descriptions)}) "
            f"[field_index NOT resolvable against the shipped codebook]"
        )
        for idx, text in list(p.descriptions.items())[:4]:
            snippet = text if len(text) <= 260 else text[:260] + "..."
            lines.append(f"   field_index {idx}: {snippet}")

    if show_evidence and p.grounding:
        unmappable = sum(
            1 for g in p.grounding.values() if not (g["index_in_range"] and g["index_is_populated"])
        )
        lines.append(
            f"\n-- Grounding ({len(p.grounding)} entries, {unmappable} with an index this "
            f"persona does not carry)"
        )
        for idx, g in list(p.grounding.items())[:5]:
            ev = (g["evidence"] or "")[:180]
            conf = g["confidence"]
            conf_s = f"{conf:.2f}" if isinstance(conf, float) else "-"
            if not g["index_in_range"]:
                flag = "OUT OF RANGE"
            elif not g["index_is_populated"]:
                flag = "index not populated in this row"
            else:
                flag = "index populated"
            lines.append(
                f"   field_index {idx}  conf={conf_s}  type={g['assignment_type']}  [{flag}]"
            )
            if ev:
                lines.append(f"      evidence: {ev}")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Decode nibble-packed personas from the MatrAIx Persona 1M release.",
        epilog=(
            "Examples:\n"
            "  %(prog)s --source amazon --limit 2\n"
            "  %(prog)s --source synthetic --limit 1 --max-attrs 60\n"
            "  %(prog)s --row 42 --evidence\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="release directory")
    parser.add_argument("--source", default=None, help="only personas from this source")
    parser.add_argument("--row", type=int, default=None, help="a single global row id")
    parser.add_argument("--limit", type=int, default=1, help="how many personas to print")
    parser.add_argument("--max-attrs", type=int, default=40, help="attribute lines per persona")
    parser.add_argument("--evidence", action="store_true", help="show grounding evidence")
    args = parser.parse_args()

    book = Codebook(args.root / "persona_codes.schema.json")
    shards = shard_table(args.root)

    if args.row is not None:
        target = next(
            (s for s in shards if s["rowStart"] <= args.row < s["rowStart"] + s["rowCount"]), None
        )
        if target is None:
            raise SystemExit(
                f"row {args.row} is outside the release (0..999846). "
                f"hint: row ids are global across all 10 shards."
            )
        local = args.row - target["rowStart"]
        table = pq.ParquetFile(args.root / target["path"]).read_row_group(0)
        # Row groups are ~1,350 rows; walk batches rather than assume one group holds it.
        pf = pq.ParquetFile(args.root / target["path"])
        seen = 0
        for batch in pf.iter_batches(batch_size=2048):
            rows = batch.to_pylist()
            if seen + len(rows) > local:
                row = rows[local - seen]
                print(render(decode_row(row, args.row, book), book, args.max_attrs, args.evidence))
                return 0
            seen += len(rows)
        raise SystemExit(f"row {args.row} not reached in {target['path']}")

    count = 0
    for persona in iter_rows(args.root, book, shards, args.source, args.limit):
        print(render(persona, book, args.max_attrs, args.evidence))
        count += 1
    if count == 0:
        raise SystemExit(
            f"no personas matched source={args.source!r}. "
            f"hint: valid sources are wiki, amazon, stackoverflow, gss, prism, "
            f"real_human_survey, synthetic."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
