# File: gguf_ctx_probe.py
# Purpose: Read architecture and n_ctx_train from GGUF headers without loading the model.
# Project: sparkbench | Date: 2026-07-04
#
# Overview: Pure-stdlib GGUF metadata parser (llama.cpp's gguf-py needs numpy,
# absent on this host). Walks the header's key-value section sequentially -
# magic, version, tensor count, kv count, then typed kv pairs - collecting
# general.architecture and {arch}.context_length. Used by the Step 8
# depth-curve gate (PHASE-A-LOG step 8 pre-registration): a depth leg of
# 32768 is included only where n_ctx_train >= 32896. Reads only header
# bytes, never tensor data - safe to run beside nothing and cheap enough
# to run between bench legs.

from __future__ import annotations

import argparse
import struct
import sys
from typing import Any, BinaryIO

# GGUFValueType per llama.cpp gguf spec
_SCALARS: dict[int, tuple[str, int]] = {
    0: ("<B", 1),   # UINT8
    1: ("<b", 1),   # INT8
    2: ("<H", 2),   # UINT16
    3: ("<h", 2),   # INT16
    4: ("<I", 4),   # UINT32
    5: ("<i", 4),   # INT32
    6: ("<f", 4),   # FLOAT32
    7: ("<B", 1),   # BOOL
    10: ("<Q", 8),  # UINT64
    11: ("<q", 8),  # INT64
    12: ("<d", 8),  # FLOAT64
}
_STRING = 8
_ARRAY = 9

GATE_MIN_CTX = 32896  # 32768 depth + 128 generated tokens


def _read_exact(f: BinaryIO, n: int) -> bytes:
    data = f.read(n)
    if len(data) != n:
        raise ValueError(
            f"truncated GGUF header (wanted {n} bytes, got {len(data)}); "
            "hint: file may be a partial download - re-verify against the manifest"
        )
    return data


def _read_string(f: BinaryIO) -> str:
    (length,) = struct.unpack("<Q", _read_exact(f, 8))
    return _read_exact(f, length).decode("utf-8", errors="replace")


def _read_value(f: BinaryIO, vtype: int) -> Any:
    if vtype in _SCALARS:
        fmt, size = _SCALARS[vtype]
        (val,) = struct.unpack(fmt, _read_exact(f, size))
        return bool(val) if vtype == 7 else val
    if vtype == _STRING:
        return _read_string(f)
    if vtype == _ARRAY:
        (elem_type,) = struct.unpack("<I", _read_exact(f, 4))
        (count,) = struct.unpack("<Q", _read_exact(f, 8))
        return [_read_value(f, elem_type) for _ in range(count)]
    raise ValueError(
        f"unknown GGUF value type {vtype}; "
        "hint: file may use a newer GGUF revision than this parser knows"
    )


def read_metadata(path: str) -> dict[str, Any]:
    with open(path, "rb") as f:
        if _read_exact(f, 4) != b"GGUF":
            raise ValueError(
                f"{path} is not a GGUF file (bad magic); "
                "hint: check the path points at a .gguf artefact"
            )
        (version,) = struct.unpack("<I", _read_exact(f, 4))
        if version < 2:
            raise ValueError(
                f"GGUF v{version} uses 32-bit counts this parser does not handle; "
                "hint: v1 artefacts predate 2023 - not expected in this store"
            )
        _tensor_count, kv_count = struct.unpack("<QQ", _read_exact(f, 16))
        meta: dict[str, Any] = {}
        for _ in range(kv_count):
            key = _read_string(f)
            (vtype,) = struct.unpack("<I", _read_exact(f, 4))
            meta[key] = _read_value(f, vtype)
        return meta


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print arch, n_ctx_train, and the 32768-depth gate verdict per GGUF.",
        epilog="Example: python3 tools/gguf_ctx_probe.py /opt/models/staging/*.gguf",
    )
    parser.add_argument("paths", nargs="+", help="GGUF file paths")
    args = parser.parse_args()

    failures = 0
    for path in args.paths:
        try:
            meta = read_metadata(path)
        except (OSError, ValueError) as exc:
            print(f"{path}: ERROR {exc}", file=sys.stderr)
            failures += 1
            continue
        arch = meta.get("general.architecture", "?")
        n_ctx = meta.get(f"{arch}.context_length")
        verdict = (
            "INCLUDE-32768"
            if isinstance(n_ctx, int) and n_ctx >= GATE_MIN_CTX
            else "EXCLUDE-32768"
        )
        print(f"{path}: arch={arch} n_ctx_train={n_ctx} -> {verdict}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
