#!/usr/bin/env python3
# File: tts-bench/speakable.py
# Purpose: Turn numerals, years, ordinals and dates into the WORDS a TTS engine must be given, because
#          Chatterbox does no number handling of its own.
# Project: sparkbench | Date: 2026-07-26
#
# Overview: Verified against the installed Chatterbox package, not assumed: `punc_norm` rewrites
# punctuation only, and its tokenizer module contains zero occurrences of num2words / inflect / digit /
# ordinal logic. Numerals therefore reach the model raw, and what it says is unpredictable learned
# behaviour. The intelligibility gate cannot cover for this either - Whisper renormalises spoken numbers
# back into numerals, so "two hundred and thirty percent" and "two three zero percent" both transcribe
# as "230%", scoring identically. tests/test_speakable.py is the only real check on this layer.
#
# Owner requirement (2026-07-26): published dates are spoken as ORDINALS - "the eighteenth of April",
# never "eighteen". Implemented in `ordinal` + `spoken_date`, in British day-month-year order.
#
# Design: stdlib only. num2words, inflect and bs4 are all absent on this host, and adding a dependency
# to render 30 blog posts is not worth a pinned-version decision when the spell-out is 60 testable lines.
#
# Order of operations inside `numbers_to_words` matters and is the main source of subtle bugs: dates
# before bare years (else "2026-07-19" has its year eaten first), currency before plain integers (else
# the symbol is orphaned), percentages before integers, and comma-thousands before anything that would
# split on the comma. Each rule is anchored so it cannot fire inside a longer token.
from __future__ import annotations

import re

_UNITS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
          "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen",
          "nineteen"]
_TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
# Irregular ordinals. A naive "cardinal + th" breaks on every one of these, which is why they are a
# table rather than a rule.
_ORD_IRREGULAR = {"one": "first", "two": "second", "three": "third", "five": "fifth",
                  "eight": "eighth", "nine": "ninth", "twelve": "twelfth"}
_MONTHS = ["January", "February", "March", "April", "May", "June",
           "July", "August", "September", "October", "November", "December"]
_MONTH_NUM = {m.lower(): i + 1 for i, m in enumerate(_MONTHS)}
_CURRENCY = {"£": ("pound", "pounds"), "$": ("dollar", "dollars"), "€": ("euro", "euros")}
# Magnitude words that attach to a money amount, either spelled ("$4 billion") or as a suffix letter
# ("$4B", "€30k"). English puts the magnitude BEFORE the currency word - "four billion dollars", never
# "four dollars billion" - so the money rule has to absorb it rather than leave it stranded.
# Longer suffixes precede their prefixes in the alternation below, so "bn" is not read as "b".
_MAGNITUDE_SUFFIX = {"k": "thousand", "m": "million", "b": "billion", "bn": "billion",
                     "t": "trillion", "tn": "trillion"}
_MAGNITUDE_WORDS = ("thousand", "million", "billion", "trillion")


def cardinal(n: int) -> str:
    """Spell a non-negative integer below 10^12. Raises rather than truncating a larger value."""
    if n < 0:
        raise ValueError(
            f"cardinal() received a negative value ({n}). "
            f"hint: strip the sign and speak it as 'minus' at the call site, so the caller decides "
            f"whether a bare minus makes sense in context."
        )
    if n >= 10 ** 12:
        raise ValueError(
            f"cardinal() supports values below 10^12; got {n}. "
            f"hint: a number this large in prose is almost certainly a year, an ID or a typo - handle "
            f"it explicitly at the call site rather than spelling it out."
        )
    if n < 20:
        return _UNITS[n]
    if n < 100:
        return _TENS[n // 10] + ("" if n % 10 == 0 else f"-{_UNITS[n % 10]}")
    for size, name in ((10 ** 9, "billion"), (10 ** 6, "million"), (1000, "thousand"), (100, "hundred")):
        if n >= size:
            head = f"{cardinal(n // size)} {name}"
            rest = n % size
            if not rest:
                return head
            # "and" only bridges a sub-hundred remainder: "one thousand and one", but
            # "one thousand five hundred" - which is how it is said aloud.
            joiner = " and " if rest < 100 else " "
            return head + joiner + cardinal(rest)
    raise AssertionError(f"unreachable: {n}")  # every branch above returns


def ordinal(n: int) -> str:
    """Spell an ordinal ('eighteenth'). Only the FINAL word inflects: 'twenty-first', not 'twentieth-first'."""
    words = cardinal(n)
    head, _, last = words.rpartition("-")
    if last in _ORD_IRREGULAR:
        tail = _ORD_IRREGULAR[last]
    elif last.endswith("y"):
        tail = last[:-1] + "ieth"          # twenty -> twentieth
    else:
        tail = last + "th"
    return f"{head}-{tail}" if head else tail


def year(y: int) -> str:
    """Speak a year the way it is said, which is not its cardinal form.

    2024 is "twenty twenty-four", not "two thousand and twenty-four". The 2000-2009 decade is the
    exception: those ARE said as "two thousand and five", which is why a plain pair-split is wrong.
    """
    if not 1000 <= y <= 2999:
        return cardinal(y)
    hi, lo = divmod(y, 100)
    if y % 1000 == 0:
        return cardinal(y)                       # 2000 -> "two thousand"
    if 2000 < y < 2010:
        return f"two thousand and {_UNITS[lo]}"  # 2005 -> "two thousand and five"
    if lo == 0:
        return f"{cardinal(hi)} hundred"         # 1900 -> "nineteen hundred"
    return f"{cardinal(hi)} {cardinal(lo)}" if lo >= 10 else f"{cardinal(hi)} oh {_UNITS[lo]}"


def spoken_date(value: str) -> str:
    """ISO date (or WP API datetime) -> "the nineteenth of July, twenty twenty-six"."""
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})(?:[T ].*)?$", value.strip())
    if not m:
        raise ValueError(
            f"spoken_date() expected an ISO date like '2026-07-19' or '2026-07-19T21:05:20'; "
            f"got {value!r}. "
            f"hint: pass the WordPress API's `date` field verbatim - do not pre-format it, and do not "
            f"pass free text, because there is no safe way to guess what date it means."
        )
    y_, mo, d = int(m[1]), int(m[2]), int(m[3])
    if not 1 <= mo <= 12:
        raise ValueError(
            f"month {mo} out of range in {value!r}. "
            f"hint: the API returns zero-padded months; a value outside 1-12 means the string was "
            f"reformatted somewhere upstream."
        )
    return f"the {ordinal(d)} of {_MONTHS[mo - 1]}, {year(y_)}"


def typography(text: str) -> str:
    """Flatten smart punctuation. Same map as tools/chatterbox_tts.py, kept in step with it."""
    for a, b in (("—", " - "), ("–", "-"), ("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'),
                 ("…", "..."), (" ", " "), ("‑", "-")):
        text = text.replace(a, b)
    return " ".join(text.split())


def _decimal(whole: str, frac: str) -> str:
    return f"{cardinal(int(whole))} point {' '.join(_UNITS[int(c)] for c in frac)}"


def _is_year(tok: str) -> bool:
    """Whether a bare token should be spoken as a year rather than a cardinal."""
    return bool(re.fullmatch(r"1[89]\d{2}|20\d{2}", tok))


def _num(tok: str) -> str:
    """Spell a numeric token that may carry comma separators or a decimal part."""
    tok = tok.replace(",", "")
    if "." in tok:
        whole, _, frac = tok.partition(".")
        return _decimal(whole or "0", frac)
    return cardinal(int(tok))


# Unit suffixes that may be glued to a number. Anything NOT listed here leaves its token untouched and
# is reported by `unhandled()`, rather than being guessed at - see _classify's contract.
_UNITS_SUFFIX = {
    "mb": "megabytes", "gb": "gigabytes", "kb": "kilobytes", "tb": "terabytes",
    "kwh": "kilowatt hours", "mwh": "megawatt hours", "kw": "kilowatts", "mw": "megawatts",
    "gw": "gigawatts", "w": "watts", "ml": "millilitres", "l": "litres", "kg": "kilograms",
    "g": "grams", "km": "kilometres", "m": "metres", "cm": "centimetres", "mm": "millimetres",
    "s": "seconds", "ms": "milliseconds", "h": "hours", "hz": "hertz", "k": "thousand",
    "am": "a.m.", "pm": "p.m.", "x": "times", "b": "billion",
}
# A token containing a digit, taken whole. Classification is per-token and ATOMIC: layered re.sub passes
# backtrack and corrupt ("1,000x" -> "one,000x"), which is worse than leaving the token alone.
#
# The lookbehind requires a genuine token START. Without it the match begins mid-token - the leading
# [A-Za-z_]* cannot cross the hyphen in "GPT-4", so the match started at the digit and produced
# "GPT-four"; guarding only the hyphen then let "GPT-5.2" match at the "2" and give "GPT-5.two". A
# number in prose is always preceded by whitespace, a bracket, a quote or a currency symbol - never by a
# word character, dot, apostrophe or hyphen.
_NUMERIC_RE = re.compile(r"(?<![\w.'-])[A-Za-z_]*[\d][\w.,:%/'-]*")
_TRAIL = ".,;:!?)]}\"'"
_POSSESSIVE = re.compile(r"('s|’s)$")


def _classify(tok: str) -> str | None:
    """Speak one digit-bearing token, or return None meaning 'leave it exactly as it is'.

    None is the safe answer and is used deliberately: a product name (GPT-4), a version (v7), a
    filename or an unrecognised unit is better read as-written than half-rewritten. Callers surface the
    Nones via `unhandled()` so the set is auditable rather than silent.
    """
    if re.match(r"^\d{4}-\d{2}-\d{2}$", tok):
        return spoken_date(tok)
    if re.match(r"^[A-Za-z_]", tok):                     # GPT-4, v7, Final_FINAL_v7, H100
        return None
    m = re.fullmatch(r"(\d+(?:,\d{3})*(?:\.\d+)?)\s?%", tok)
    if m:
        return f"{_num(m[1])} percent"
    m = re.fullmatch(r"(\d{1,3}(?:,\d{3})*|\d+)(st|nd|rd|th)", tok)
    if m:
        return ordinal(int(m[1].replace(",", "")))
    # Ranges and compounds, both hyphen-joined: "10-15" vs "20-minute".
    #
    # The range may carry the unit on its SECOND number only - "25-30%", "10-15k". Reading that as a
    # bare range dropped the unit entirely and left "25-30%" untouched in the script, so the engine was
    # handed a raw numeral. Owner's reading, 2026-07-28: "twenty-five to thirty percent".
    # "20-minute" cannot reach here - it has no second number - so the digit-hyphen-WORD rule below
    # still owns compounds.
    m = re.fullmatch(r"(\d+(?:,\d{3})*)-(\d+(?:,\d{3})*)(%|[A-Za-z]+)?", tok)
    if m:
        a, b, suffix = m[1].replace(",", ""), m[2].replace(",", ""), m[3]
        if suffix is None:
            if _is_year(a) and _is_year(b):
                return f"{year(int(a))} to {year(int(b))}"
            return f"{_num(a)} to {_num(b)}"
        if suffix == "%":
            return f"{_num(a)} to {_num(b)} percent"
        unit = _UNITS_SUFFIX.get(suffix.lower())
        # An unrecognised unit returns None, same contract as the single-number case: better read
        # as-written and surfaced by unhandled() than half-rewritten.
        return None if unit is None else f"{_num(a)} to {_num(b)} {unit}"
    m = re.fullmatch(r"(\d+(?:,\d{3})*)-([A-Za-z][\w-]*)", tok)
    if m:                                                 # "20-minute", "85-ton", "12-axle"
        return f"{_num(m[1])}-{m[2]}"
    m = re.fullmatch(r"(\d+(?:,\d{3})*(?:\.\d+)?)([A-Za-z]+)", tok)
    if m:                                                 # "50MB", "8am", "100x", "0.26mL"
        unit = _UNITS_SUFFIX.get(m[2].lower())
        return None if unit is None else f"{_num(m[1])} {unit}"
    if tok == "24/7":                                     # idiomatic; other slashed forms are ambiguous
        return "twenty-four seven"
    if _is_year(tok):
        return year(int(tok))
    if re.fullmatch(r"\d+(?:,\d{3})*(?:\.\d+)?", tok):
        return _num(tok)
    return None


def _rewrite_tokens(text: str, seen_unhandled: set[str] | None = None) -> str:
    """Replace each digit-bearing token via _classify, preserving trailing punctuation."""
    def sub(m: re.Match[str]) -> str:
        raw = m.group(0)
        core = raw.rstrip(_TRAIL)
        tail = raw[len(core):]
        # A possessive year ("2024's lesson") is a number plus a suffix, not an unclassifiable token.
        poss = _POSSESSIVE.search(core)
        if poss:
            core, tail = core[:poss.start()], poss.group(0) + tail
        spoken = _classify(core)
        if spoken is None:
            if seen_unhandled is not None:
                seen_unhandled.add(core)
            return raw
        return spoken + tail

    return _NUMERIC_RE.sub(sub, text)


def numbers_to_words(text: str, seen_unhandled: set[str] | None = None) -> str:
    """Rewrite every numeral form found in the real post corpus into words.

    Two phases. Multi-token dates and currency are handled first because they span a boundary a
    single-token pass cannot see; everything else goes through one atomic token pass.
    """
    # Phase 1: forms that span more than one token.

    # A "+" glued to a number means "or more" (owner decision, 2026-07-28). Run FIRST so the currency
    # rule below still sees a clean "$500M" and the "+" does not end up stranded after the unit.
    #
    # It must key off a DIGIT, never a letter: the corpus contains "Ctrl+" (a keyboard shortcut), which
    # must survive untouched. The leading lookbehind is the same token-start guard _NUMERIC_RE uses, and
    # the trailing (?!\d) stops "2+2" becoming "two or more2".
    text = re.sub(r"(?<![\w.'-])(\d[\d,.]*[A-Za-z]*)\+(?!\d)", r"\1 or more", text)

    text = re.sub(rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+({'|'.join(_MONTHS)})\s+(\d{{4}})\b",
                  lambda m: f"the {ordinal(int(m[1]))} of {m[2]}, {year(int(m[3]))}", text,
                  flags=re.IGNORECASE)
    text = re.sub(rf"\b({'|'.join(_MONTHS)})\s+(\d{{1,2}})(?:st|nd|rd|th)?,?\s+(\d{{4}})\b",
                  lambda m: f"the {ordinal(int(m[2]))} of {m[1]}, {year(int(m[3]))}", text,
                  flags=re.IGNORECASE)
    # A word-hyphen-YEAR compound ("mid-2024", "post-1999"). The token pass cannot reach these: its
    # lookbehind rejects a match preceded by a hyphen, which is exactly what protects "GPT-4". The
    # discriminator is that the digits form a plausible YEAR - "GPT-4" and "COVID-19" do not, so they
    # stay untouched while a real year is still spoken.
    text = re.sub(r"\b([A-Za-z]+)-(1[89]\d{2}|20\d{2})\b",
                  lambda m: f"{m[1]}-{year(int(m[2]))}", text)

    # Currency: the symbol sits OUTSIDE the token, and a range keeps the unit ("$5-10" -> "five to ten
    # dollars"), which the token pass alone would render "five dollars to ten".
    #
    # The rule must also swallow any MAGNITUDE that follows, because English orders it before the
    # currency word. Matching only the numeral left the magnitude stranded on the far side of the unit:
    # "$260 million" -> "two hundred and sixty dollars million", "$62M" -> "sixty-two dollarsM". The WER
    # gate is structurally blind to both, since Whisper renormalises them back to "$260 million".
    def _money(m: re.Match[str]) -> str:
        sym, lo, hi, suffix, word = m[1], m[2], m[3], m[4], m[5]
        single, plural = _CURRENCY[sym]
        mag = _MAGNITUDE_SUFFIX[suffix.lower()] if suffix else (word.lower() if word else "")
        head = f"{_num(lo)} to {_num(hi)}" if hi else _num(lo)
        # A magnitude always pluralises the unit: "$1 million" is "one million dollars", not "dollar".
        unit = single if (not mag and not hi and lo.replace(",", "") in ("1", "1.0")) else plural
        return f"{head} {mag} {unit}" if mag else f"{head} {unit}"

    text = re.sub(rf"([{''.join(_CURRENCY)}])\s?(\d+(?:,\d{{3}})*(?:\.\d+)?)"
                  rf"(?:\s?-\s?(\d+(?:,\d{{3}})*(?:\.\d+)?))?"
                  # Suffix must sit flush against the digits ("$4B"); a spelled magnitude may be spaced
                  # or not ("$4 billion", "$4billion"). \b on both stops "billionaires" being eaten and
                  # stops "$500Million" matching the bare "M" branch.
                  rf"(?:({'|'.join(sorted(_MAGNITUDE_SUFFIX, key=len, reverse=True))})\b"
                  rf"|\s*({'|'.join(_MAGNITUDE_WORDS)})\b)?",
                  _money, text, flags=re.IGNORECASE)

    # Phase 2: one atomic pass over every remaining digit-bearing token.
    return _rewrite_tokens(text, seen_unhandled)


def unhandled(text: str) -> set[str]:
    """Digit-bearing tokens still present AFTER normalisation - i.e. digits the listener will hear.

    Deliberately measured on the OUTPUT rather than by instrumenting the skip path. A name like "GPT-4"
    never enters the token pass at all (the lookbehind excludes it), so a skip-path counter would report
    it as handled. What the batch audit needs is the honest question: what digits survive to the engine?
    """
    out = speakable(text)
    return {t for t in out.split() if any(c.isdigit() for c in t)}


# Top-level domains, split by how they are SAID. Two-letter TLDs are spelled out letter by letter
# ("dot A I"); pronounceable ones are said as words ("dot com"). Both sets are drawn from a scan of the
# real corpus - humanspark.ai, Rev.ai, ChatGPT.com, Amazon.com, Amazon.co.uk - plus the obvious
# neighbours. Membership of these sets is the ONLY thing that makes a dotted token a domain, which is
# what keeps P.S / e.g / i.e / a.m / 5.x / GPT-3.5 / do.ts out of the rule.
_TLD_SPELL = {"ai": "A I", "io": "I O", "uk": "U K", "ie": "I E", "us": "U S", "eu": "E U",
              "tv": "T V", "fm": "F M", "de": "D E", "nl": "N L"}
_TLD_WORD = {"com", "net", "org", "co", "dev", "app", "info", "blog", "news", "shop", "cloud"}
_DOTTED = re.compile(r"\b([A-Za-z0-9][A-Za-z0-9-]*(?:\.[A-Za-z0-9-]+)+)")


def _spoken_label(label: str) -> str:
    low = label.lower()
    if low in _TLD_SPELL:
        return _TLD_SPELL[low]
    return label


def domains_to_words(text: str) -> str:
    """Speak a domain as "name dot A I". Non-domain dotted tokens are returned untouched.

    A token qualifies only if its FINAL label is a known TLD. That test is what protects this
    module's own output: `numbers_to_words` turns "8am" into "eight a.m.", and a rule keyed on any
    dotted token would immediately corrupt it.
    """
    def sub(m: re.Match[str]) -> str:
        tok = m.group(1)
        labels = tok.split(".")
        if labels[-1].lower() not in _TLD_SPELL and labels[-1].lower() not in _TLD_WORD:
            return tok
        return " dot ".join([labels[0]] + [_spoken_label(x) for x in labels[1:]])

    return _DOTTED.sub(sub, text)


def repair_sentence_spacing(text: str) -> str:
    """Insert the missing space in "shoulder.This" - a real typo in two published posts.

    Left alone these are unsplittable: the chunker breaks on `[.!?]` followed by WHITESPACE, so the
    two sentences render as one run-on chunk and the engine sees a single fused token. Triggering only
    on a following CAPITAL keeps domains ("humanspark.ai") and versions ("5.x", "GPT-3.5") untouched.
    """
    return re.sub(r"(?<=[a-z])\.(?=[A-Z])", ". ", text)


def speakable(text: str) -> str:
    """The full text-level pass, in the one order that is safe.

    Typography first (so quotes and dashes are flat), then the sentence-boundary repair, then domains,
    and numerals LAST - because numbers_to_words emits dotted output of its own ("eight a.m.") that
    the domain rule must never see as an input.
    """
    return numbers_to_words(domains_to_words(repair_sentence_spacing(typography(text))))
