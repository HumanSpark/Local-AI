# File: tests/test_speakable.py
# Purpose: Tests for the TTS text-speakability layer - numbers, years, ordinals and dates as WORDS.
# Project: sparkbench | Date: 2026-07-26
#
# Overview: This layer is load-bearing, not cosmetic. Chatterbox has NO number handling whatsoever -
# `punc_norm` only rewrites punctuation, and its tokenizer contains no num2words / inflect / digit /
# ordinal logic (verified by inspecting the installed package: 0 hits for each). Digits therefore reach
# the model raw and whatever it says is unverifiable learned behaviour. Worse, the intelligibility gate
# CANNOT catch a misread number: Whisper renormalises spoken numbers back into numerals, so
# "two hundred and thirty percent" and "two three zero percent" both transcribe as "230%". These tests
# are the only check on this behaviour, which is why they are unusually thorough about boundaries.
#
# The owner's explicit requirement: published dates are read as ORDINALS - "the eighteenth of April",
# never "eighteen". Covered by test_ordinal_words and test_iso_date_reads_as_ordinal_british_form.
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tts-bench"))
import speakable as sp  # noqa: E402


@pytest.mark.parametrize(("n", "want"), [
    (0, "zero"), (1, "one"), (9, "nine"), (10, "ten"), (11, "eleven"), (12, "twelve"),
    (13, "thirteen"), (15, "fifteen"), (19, "nineteen"), (20, "twenty"), (21, "twenty-one"),
    (30, "thirty"), (42, "forty-two"), (50, "fifty"), (99, "ninety-nine"),
    (100, "one hundred"), (101, "one hundred and one"), (110, "one hundred and ten"),
    (230, "two hundred and thirty"), (999, "nine hundred and ninety-nine"),
    (1000, "one thousand"), (1001, "one thousand and one"), (1500, "one thousand five hundred"),
    (37000, "thirty-seven thousand"), (95000, "ninety-five thousand"),
    (100000, "one hundred thousand"), (1000000, "one million"),
    (2500000, "two million five hundred thousand"),
])
def test_cardinal(n: int, want: str) -> None:
    assert sp.cardinal(n) == want


@pytest.mark.parametrize(("n", "want"), [
    # The owner's requirement, boundary by boundary. The -th/-st/-nd/-rd irregulars are where a
    # naive "append th" implementation breaks, so every irregular form in 1..31 is pinned.
    (1, "first"), (2, "second"), (3, "third"), (4, "fourth"), (5, "fifth"),
    (6, "sixth"), (7, "seventh"), (8, "eighth"), (9, "ninth"), (10, "tenth"),
    (11, "eleventh"), (12, "twelfth"), (13, "thirteenth"), (14, "fourteenth"),
    (15, "fifteenth"), (16, "sixteenth"), (17, "seventeenth"), (18, "eighteenth"),
    (19, "nineteenth"), (20, "twentieth"), (21, "twenty-first"), (22, "twenty-second"),
    (23, "twenty-third"), (24, "twenty-fourth"), (25, "twenty-fifth"), (26, "twenty-sixth"),
    (27, "twenty-seventh"), (28, "twenty-eighth"), (29, "twenty-ninth"),
    (30, "thirtieth"), (31, "thirty-first"),
])
def test_ordinal_words(n: int, want: str) -> None:
    assert sp.ordinal(n) == want


@pytest.mark.parametrize(("y", "want"), [
    (1999, "nineteen ninety-nine"),
    (1984, "nineteen eighty-four"),
    (1900, "nineteen hundred"),
    (2000, "two thousand"),
    (2005, "two thousand and five"),
    (2009, "two thousand and nine"),
    (2010, "twenty ten"),
    (2024, "twenty twenty-four"),
    (2025, "twenty twenty-five"),
    (2026, "twenty twenty-six"),
    (2100, "twenty-one hundred"),
])
def test_year(y: int, want: str) -> None:
    """Years are NOT read as plain cardinals - 2024 is 'twenty twenty-four', not 'two thousand and
    twenty-four'. The 2000-2009 decade is the exception that breaks a naive pair-splitting rule."""
    assert sp.year(y) == want


def test_iso_date_reads_as_ordinal_british_form() -> None:
    assert sp.spoken_date("2026-07-19") == "the nineteenth of July, twenty twenty-six"
    assert sp.spoken_date("2026-04-18") == "the eighteenth of April, twenty twenty-six"
    assert sp.spoken_date("2025-12-01") == "the first of December, twenty twenty-five"
    assert sp.spoken_date("2025-10-02") == "the second of October, twenty twenty-five"


def test_iso_datetime_from_wp_api_is_accepted() -> None:
    """The WordPress REST API returns '2026-07-19T21:05:20'; the time must be discarded, not read."""
    assert sp.spoken_date("2026-07-19T21:05:20") == "the nineteenth of July, twenty twenty-six"


def test_spoken_date_rejects_garbage_rather_than_inventing_one() -> None:
    with pytest.raises(ValueError, match="hint"):
        sp.spoken_date("last Tuesday")


@pytest.mark.parametrize(("raw", "want"), [
    ("230%", "two hundred and thirty percent"),
    ("17%", "seventeen percent"),
    ("95%", "ninety-five percent"),
    ("3.5%", "three point five percent"),
])
def test_percentages(raw: str, want: str) -> None:
    assert sp.numbers_to_words(raw) == want


@pytest.mark.parametrize(("raw", "want"), [
    ("37,000 people", "thirty-seven thousand people"),
    ("1,500 words", "one thousand five hundred words"),
    ("in 12 months", "in twelve months"),
    ("GPT-4", "GPT-4"),                        # hyphenated product names are left alone
    ("the 1st time", "the first time"),
    ("the 2nd and 3rd", "the second and third"),
    ("21st century", "twenty-first century"),
    ("3.5 hours", "three point five hours"),
    ("£100", "one hundred pounds"),
    ("$1,000", "one thousand dollars"),
    ("€50", "fifty euros"),
])
def test_inline_numbers(raw: str, want: str) -> None:
    assert sp.numbers_to_words(raw) == want


def test_bare_year_in_prose_reads_as_a_year_not_a_cardinal() -> None:
    assert sp.numbers_to_words("in late 2024.") == "in late twenty twenty-four."
    assert sp.numbers_to_words("since 1999") == "since nineteen ninety-nine"


@pytest.mark.parametrize(("raw", "want"), [
    # Regression: the year rule's lookahead once excluded a following '.' or ',' to avoid decimals,
    # which silently sent every sentence-final and clause-final year to the plain-cardinal rule.
    ("in late 2024.", "in late twenty twenty-four."),
    ("in 2024, we saw", "in twenty twenty-four, we saw"),
    ("by 2026; then", "by twenty twenty-six; then"),
    ("(2025)", "(twenty twenty-five)"),
    ("2024's lesson", "twenty twenty-four's lesson"),
])
def test_year_survives_adjacent_sentence_punctuation(raw: str, want: str) -> None:
    assert sp.numbers_to_words(raw) == want


def test_year_ranges_read_as_years_not_cardinals() -> None:
    assert sp.numbers_to_words("2024-2025 was") == \
        "twenty twenty-four to twenty twenty-five was"


def test_decimal_is_not_mistaken_for_a_year() -> None:
    assert sp.numbers_to_words("2024.5 units") == "two thousand and twenty-four point five units"


def test_written_dates_in_prose_become_ordinal() -> None:
    assert sp.numbers_to_words("on 19 July 2026") == "on the nineteenth of July, twenty twenty-six"
    assert sp.numbers_to_words("on July 19, 2026") == "on the nineteenth of July, twenty twenty-six"
    assert sp.numbers_to_words("by 1 January 2027") == "by the first of January, twenty twenty-seven"


def test_iso_date_inside_prose_is_expanded_not_read_as_digits() -> None:
    """The probe showed a raw ISO date survives into the audio as something machine-shaped; this is the
    case that most obviously must not reach the listener."""
    assert sp.numbers_to_words("published 2026-07-19 online") == \
        "published the nineteenth of July, twenty twenty-six online"


def test_number_ranges_and_versions_do_not_lose_their_separator() -> None:
    assert sp.numbers_to_words("10-15 people") == "ten to fifteen people"


@pytest.mark.parametrize(("raw", "want"), [
    # REGRESSION SET, all found by auditing the real 30-post corpus. Each of these was previously
    # CORRUPTED rather than merely skipped: layered re.sub passes backtracked to a shorter match,
    # spelled the fragment, and orphaned the rest - producing output no listener could decode.
    ("1,000x", "one thousand times"),          # was "one,000x"
    ("4,300x", "four thousand three hundred times"),   # was "four,300x"
    ("0.26mL", "zero point two six millilitres"),      # was "zero.26mL"
    ("$5-10", "five to ten dollars"),          # was "five dollars-10"
    ("100x", "one hundred times"),
    ("50MB", "fifty megabytes"),
    ("8am", "eight a.m."),
    ("20-minute", "twenty-minute"),
    ("85-ton", "eighty-five-ton"),
    ("200-page", "two hundred-page"),
])
def test_units_multipliers_and_compounds_are_atomic(raw: str, want: str) -> None:
    assert sp.numbers_to_words(raw) == want


@pytest.mark.parametrize(("raw", "want"), [
    # CURRENCY + MAGNITUDE. Every raw string below is lifted verbatim from var/posts/raw. The money rule
    # consumed only the numeral, so the magnitude - a following word or an attached k/M/B - was orphaned
    # AFTER the currency word: "$260 million" was spoken "two hundred and sixty DOLLARS MILLION" and
    # "$62M" became "sixty-two DOLLARSM". Found by the 2026-07-28 STT spot check on post 0075, then swept
    # across the corpus: 17 occurrences in 7 posts, none of which the WER gate could ever see, because
    # Whisper renormalises the spoken form straight back to "$260 million" and scores it clean.
    ("$260 million", "two hundred and sixty million dollars"),
    ("$500 million", "five hundred million dollars"),
    ("$4 billion", "four billion dollars"),
    ("$1.5 billion", "one point five billion dollars"),
    ("$3 trillion", "three trillion dollars"),
    ("$4B", "four billion dollars"),
    ("$62M", "sixty-two million dollars"),
    ("$2.4M", "two point four million dollars"),
    ("€50k", "fifty thousand euros"),
    ("£53k", "fifty-three thousand pounds"),
    ("$8-10 billion", "eight to ten billion dollars"),   # range keeps ONE magnitude and ONE unit
    ("$1 million", "one million dollars"),               # plural unit, even though the numeral is 1
    # A trailing "+" reads as "or more" (owner decision, 2026-07-28).
    ("$500M+", "five hundred million dollars or more"),
    ("€30k+", "thirty thousand euros or more"),
])
def test_currency_magnitude_is_spoken_in_the_right_order(raw: str, want: str) -> None:
    assert sp.numbers_to_words(raw) == want


@pytest.mark.parametrize(("raw", "want"), [
    # Guards for the forms the magnitude fix must NOT disturb.
    ("$1", "one dollar"),                                # singular survives
    ("$1,000", "one thousand dollars"),
    ("$5-10", "five to ten dollars"),                    # range with no magnitude
    ("£100", "one hundred pounds"),
    ("€250,000", "two hundred and fifty thousand euros"),
    ("5 million users", "five million users"),           # magnitude with no currency symbol
    ("$5 billionaires", "five dollars billionaires"),    # "billion" must not be eaten out of a word
])
def test_currency_magnitude_fix_does_not_overreach(raw: str, want: str) -> None:
    assert sp.numbers_to_words(raw) == want


@pytest.mark.parametrize("tok", ["GPT-4", "GPT-3.5", "GPT-5.2", "H100", "v7", '"Final_FINAL_v7"'])
def test_names_and_versions_are_left_exactly_as_written(tok: str) -> None:
    """A product name half-rewritten is worse than one left alone. These must pass through untouched -
    'GPT-4' became 'GPT-four' when the token match started at the digit instead of the name."""
    assert sp.numbers_to_words(tok) == tok


def test_unhandled_reports_what_was_deliberately_skipped() -> None:
    """The skip path must be auditable, not silent - that is the whole reason it is safe to have one."""
    assert sp.unhandled("GPT-4 and H100 and 50MB") == {"GPT-4", "H100"}  # 50MB was spoken
    assert sp.unhandled("just 12 things") == set()


def test_large_cardinal_beyond_supported_range_raises_rather_than_truncating() -> None:
    with pytest.raises(ValueError, match="hint"):
        sp.cardinal(10 ** 12)


def test_typography_is_flattened_for_tts() -> None:
    assert sp.typography("it’s “quoted” — really…") == 'it\'s "quoted" - really...'


@pytest.mark.parametrize(("raw", "want"), [
    # A word-hyphen-year compound. The token pass cannot see these (its lookbehind rejects a match
    # preceded by a hyphen, which is what protects GPT-4), so they need their own pre-pass. Found by
    # auditing the real corpus: "mid-2024" would otherwise have reached the engine as digits.
    ("mid-2024.", "mid-twenty twenty-four."),
    ("post-1999 work", "post-nineteen ninety-nine work"),
    ("pre-2020 thinking", "pre-twenty twenty thinking"),
    # ...while the same shape with a non-year number stays a product name.
    ("GPT-4", "GPT-4"),
    ("COVID-19", "COVID-19"),
])
def test_word_hyphen_year_is_spoken_but_product_names_are_not(raw: str, want: str) -> None:
    assert sp.numbers_to_words(raw) == want


def test_twenty_four_seven_is_idiomatic() -> None:
    assert sp.numbers_to_words("available 24/7") == "available twenty-four seven"


# --- domains -------------------------------------------------------------------------------------
# The TLD sets and the false-positive list below are BOTH taken from the real 30-post corpus, not
# imagined: a scan of the generated scripts found humanspark.ai / Rev.ai / ChatGPT.com / Amazon.com /
# Amazon.co.uk as genuine domains, alongside P.S / P.P.P.S / e.g / i.e / a.m / 5.x / GPT-3.5 / do.ts
# as dotted tokens that must NOT be touched. `a.m` matters most - it is this module's OWN output from
# "8am", so a careless domain rule would corrupt something it had just produced correctly.

@pytest.mark.parametrize(("raw", "want"), [
    ("humanspark.ai", "humanspark dot A I"),
    ("HumanSpark.ai", "HumanSpark dot A I"),
    ("Rev.ai", "Rev dot A I"),
    ("ChatGPT.com", "ChatGPT dot com"),
    ("Amazon.com", "Amazon dot com"),
    ("Amazon.co.uk", "Amazon dot co dot U K"),
    ("see humanspark.ai.", "see humanspark dot A I."),          # sentence period survives
    ("at humanspark.ai, then", "at humanspark dot A I, then"),
])
def test_domains_are_spoken(raw: str, want: str) -> None:
    assert sp.speakable(raw) == want


@pytest.mark.parametrize("tok", ["P.S.", "P.P.S.", "P.P.P.S.", "e.g.", "i.e.", "5.x", "GPT-3.5", "do.ts"])
def test_dotted_non_domains_are_left_alone(tok: str) -> None:
    assert sp.speakable(tok) == tok


def test_the_am_pm_output_of_this_module_is_not_eaten_by_the_domain_rule() -> None:
    """Regression guard: numbers_to_words turns "8am" into "eight a.m." - a domain rule keyed on any
    dotted token would then mangle its own output."""
    assert sp.speakable("meet at 8am.") == "meet at eight a.m.."[:-1] + "."


# --- lost sentence boundaries --------------------------------------------------------------------

@pytest.mark.parametrize(("raw", "want"), [
    # Real typos in the published posts: no space after the full stop. Left alone, the chunker cannot
    # split there (it needs whitespace after .!?) so two sentences render as one run-on chunk.
    ("the shoulder.This post is", "the shoulder. This post is"),
    ("Pretty straightforward.During our", "Pretty straightforward. During our"),
])
def test_missing_space_after_full_stop_is_repaired(raw: str, want: str) -> None:
    assert sp.speakable(raw) == want


@pytest.mark.parametrize("tok", ["humanspark.ai", "Amazon.co.uk", "GPT-3.5", "5.x"])
def test_boundary_repair_does_not_split_lowercase_dotted_tokens(tok: str) -> None:
    """The repair triggers only on a CAPITAL after the dot, so domains and versions are untouched."""
    assert ". " not in sp.speakable(tok)


@pytest.mark.parametrize(("raw", "want"), [
    # RANGES KEEP THEIR UNIT, AND "+" READS AS "OR MORE". Owner decisions, 2026-07-28:
    # "twenty-five to thirty percent" and "I'd read + as 'or more'". Both were found by the same
    # corpus sweep as the currency bug and left open pending these calls; neither had been listened
    # to, and neither is visible to the WER gate - Whisper renormalises both back to "25-30%" and
    # "500+". Raw forms below are taken from var/posts/raw.
    ("25-30%", "twenty-five to thirty percent"),
    ("a 20-30% lift", "a twenty to thirty percent lift"),
    ("10-15k", "ten to fifteen thousand"),
    ("7,000+", "seven thousand or more"),
    ("20+", "twenty or more"),
    ("800+", "eight hundred or more"),
    ("100+", "one hundred or more"),
    ("$500M+", "five hundred million dollars or more"),
    ("€30k+", "thirty thousand euros or more"),
])
def test_ranges_keep_their_unit_and_plus_reads_as_or_more(raw: str, want: str) -> None:
    assert sp.numbers_to_words(raw) == want


@pytest.mark.parametrize(("raw", "want"), [
    # Guards. The corpus contains a keyboard shortcut, so "+" must key off a NUMBER, never a letter.
    ("Ctrl+C", "Ctrl+C"),
    ("Ctrl+Shift+P", "Ctrl+Shift+P"),
    ("10-15 people", "ten to fifteen people"),   # range with no unit, unchanged
    ("20-minute", "twenty-minute"),              # digit-hyphen-WORD compound, not a range
    ("30%", "thirty percent"),
    ("$5-10", "five to ten dollars"),
])
def test_range_and_plus_fixes_do_not_overreach(raw: str, want: str) -> None:
    assert sp.numbers_to_words(raw) == want
