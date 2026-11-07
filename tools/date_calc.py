# File: date_calc.py
# Purpose: the deterministic date arithmetic the H6 arm hands to a model, so the model does law and the tool does counting.
# Project: sparkbench | Date: 2026-08-19
#
# Overview: three primitives - add_period, last_day_of_month, date_diff - plus an
# OpenAI-shaped TOOL_SCHEMA and a dispatch() the harness calls. Exposed both as a
# Python API and a CLI.
#
# WHAT THIS DELIBERATELY DOES NOT DO, and it is the whole design constraint.
# There is no `limitation_deadline()`, no `dsar_deadline()`, no
# `notice_effective_date()`. A helper like that would encode the legal rule, and
# H6 would then be measuring whether we can write the answer down rather than
# whether delegating ARITHMETIC helps. The model must still decide the anchor
# date, the number of months, and whether a last-day-of-month step applies; the
# tool only counts. A test asserts these helpers are absent.
#
# WHY EVERY EDGE RAISES. F92 recorded two models miscounting a deadline to the
# same wrong day. A date tool that silently assumed midnight for a bare date, or
# echoed its input when given no period, would produce a confident wrong answer
# of exactly that shape - so each of those is a ValueError with a hint instead.
from __future__ import annotations

import argparse
import calendar
import datetime as dt
import json
from typing import Any

_DATE_FMT = "%Y-%m-%d"
_DATETIME_FMTS = ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S")


def _parse(value: str) -> tuple[dt.datetime, bool]:
    """Return (parsed, has_time). Raises rather than guessing a missing time."""
    if not isinstance(value, str):
        raise ValueError(
            f"date must be a string, got {type(value).__name__}: {value!r}. "
            f"hint: pass an ISO date 'YYYY-MM-DD' or date-time 'YYYY-MM-DDTHH:MM'"
        )
    text = value.strip()
    for fmt in _DATETIME_FMTS:
        try:
            return dt.datetime.strptime(text, fmt), True
        except ValueError:
            continue
    try:
        return dt.datetime.strptime(text, _DATE_FMT), False
    except ValueError as exc:
        raise ValueError(
            f"could not parse date {value!r}. "
            f"hint: use ISO format - 'YYYY-MM-DD' for a date, 'YYYY-MM-DDTHH:MM' "
            f"for a date and time. Prose like '3 April 2026' is not accepted, "
            f"convert it first"
        ) from exc


def _render(moment: dt.datetime, has_time: bool) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M") if has_time else moment.strftime(_DATE_FMT)


def _shift_months(moment: dt.datetime, months_total: int) -> dt.datetime:
    """Calendar-month shift, clamping to the last valid day of the target month.

    This is STAT-DP C.1's rule: the same day-number in the final month, or that
    month's LAST day where it has no day of that number. 31 January + 1 month is
    28 February, not 3 March.
    """
    zero_based = moment.month - 1 + months_total
    year = moment.year + zero_based // 12
    month = zero_based % 12 + 1
    day = min(moment.day, calendar.monthrange(year, month)[1])
    return moment.replace(year=year, month=month, day=day)


def add_period(
    date: str, years: int = 0, months: int = 0, days: int = 0, hours: int = 0
) -> str:
    """Add a period to a date. Months and years clamp to the last valid day.

    Hours run continuously and require a date-time input - a bare date has no
    time to run from, and assuming midnight would invent one.
    """
    for name, value in (
        ("years", years),
        ("months", months),
        ("days", days),
        ("hours", hours),
    ):
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(
                f"{name} must be a whole number, got {value!r}. "
                f"hint: pass an integer; fractional periods are not defined here"
            )
    if years == months == days == hours == 0:
        raise ValueError(
            f"no period given for {date!r} - all of years/months/days/hours are 0. "
            f"hint: pass at least one non-zero period, or you are asking for the "
            f"input back and should not be calling this tool"
        )

    moment, has_time = _parse(date)
    if hours and not has_time:
        raise ValueError(
            f"cannot add {hours} hours to {date!r}, which carries no time of day. "
            f"hint: pass 'YYYY-MM-DDTHH:MM'. Assuming midnight would invent a "
            f"time the record does not state"
        )

    if years or months:
        moment = _shift_months(moment, years * 12 + months)
    if days or hours:
        moment += dt.timedelta(days=days, hours=hours)
    return _render(moment, has_time)


def last_day_of_month(date: str) -> str:
    """The last calendar day of the month containing `date`."""
    moment, has_time = _parse(date)
    day = calendar.monthrange(moment.year, moment.month)[1]
    return _render(moment.replace(day=day), has_time)


def date_diff(start: str, end: str, unit: str = "days") -> int:
    """Whole units from `start` to `end`. Negative when `end` precedes `start`."""
    units = {"days", "hours"}
    if unit not in units:
        raise ValueError(
            f"unknown unit {unit!r}. "
            f"hint: one of {sorted(units)}. Month and year differences are "
            f"ambiguous by calendar and are not offered"
        )
    a, _ = _parse(start)
    b, _ = _parse(end)
    delta = b - a
    return delta.days if unit == "days" else int(delta.total_seconds() // 3600)


# TOOL_SCHEMA_V1 is the three-primitive set E67 and E68 were measured against.
# FROZEN: those results are banked against it, and adding a primitive would
# silently change the configuration they are attributed to (Rule 8 / F39).
TOOL_SCHEMA_V1: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "add_period",
            "description": (
                "Add a period to a date and return the resulting date. Months and "
                "years land on the same day-number in the target month, or on that "
                "month's last day where it has no such day (e.g. 31 January plus 1 "
                "month is 28 February). Hours run continuously including weekends "
                "and require a date-time input."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "ISO date 'YYYY-MM-DD' or date-time 'YYYY-MM-DDTHH:MM'",
                    },
                    "years": {"type": "integer", "description": "whole years to add"},
                    "months": {"type": "integer", "description": "whole months to add"},
                    "days": {"type": "integer", "description": "whole days to add"},
                    "hours": {"type": "integer", "description": "whole hours to add"},
                },
                "required": ["date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "last_day_of_month",
            "description": "Return the last calendar day of the month containing the given date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "ISO date 'YYYY-MM-DD'"}
                },
                "required": ["date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "date_diff",
            "description": "Whole days or hours from start to end. Negative if end precedes start.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start": {"type": "string", "description": "ISO date or date-time"},
                    "end": {"type": "string", "description": "ISO date or date-time"},
                    "unit": {"type": "string", "enum": ["days", "hours"]},
                },
                "required": ["start", "end"],
            },
        },
    },
]


def _is_business_day(day: dt.date, holidays: frozenset[dt.date]) -> bool:
    return day.weekday() < 5 and day not in holidays


def _holiday_set(holidays: list[str] | None) -> frozenset[dt.date]:
    out = set()
    for h in holidays or []:
        parsed, _ = _parse(h)
        out.add(parsed.date())
    return frozenset(out)


def add_business_days(date: str, days: int, holidays: list[str] | None = None) -> str:
    """Move `days` business days from `date`, excluding the starting day.

    Excluding the day of the triggering event is the ordinary professional
    convention and matches STAT-DP C.4 for calendar days. Saturdays, Sundays and
    any supplied `holidays` are skipped rather than counted. Negative counts back.
    """
    if not isinstance(days, int) or isinstance(days, bool):
        raise ValueError(
            f"days must be a whole number, got {days!r}. hint: pass an integer"
        )
    if days == 0:
        raise ValueError(
            f"add_business_days({date!r}, 0) names no movement. "
            f"hint: to test whether a date IS a business day use roll_to_business_day"
        )
    moment, has_time = _parse(date)
    hol = _holiday_set(holidays)
    step = 1 if days > 0 else -1
    remaining = abs(days)
    while remaining:
        moment += dt.timedelta(days=step)
        if _is_business_day(moment.date(), hol):
            remaining -= 1
    return _render(moment, has_time)


def roll_to_business_day(
    date: str, direction: str = "forward", holidays: list[str] | None = None
) -> str:
    """Move to the nearest business day if `date` is not one; otherwise unchanged.

    Kept separate from add_business_days on purpose: conflating "roll if needed"
    with "advance N" is how a deadline silently gains or loses a day.
    """
    if direction not in ("forward", "backward"):
        raise ValueError(
            f"unknown direction {direction!r}. "
            f"hint: 'forward' (next business day) or 'backward' (preceding one)"
        )
    moment, has_time = _parse(date)
    hol = _holiday_set(holidays)
    step = 1 if direction == "forward" else -1
    guard = 0
    while not _is_business_day(moment.date(), hol):
        moment += dt.timedelta(days=step)
        guard += 1
        if guard > 3650:
            raise ValueError(
                f"no business day within 10 years of {date!r}. "
                f"hint: the holiday list is probably wrong"
            )
    return _render(moment, has_time)


def weekday(date: str) -> str:
    """The day of the week, so a derivation can assert where a date lands."""
    moment, _ = _parse(date)
    return moment.strftime("%A")


_BUSINESS_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "add_business_days",
            "description": (
                "Move a whole number of business days from a date, excluding the "
                "starting day. Saturdays, Sundays and any supplied holidays are "
                "skipped, not counted. Negative counts backwards."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "ISO date or date-time"},
                    "days": {
                        "type": "integer",
                        "description": "business days; negative counts back",
                    },
                    "holidays": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "ISO dates treated as non-business days",
                    },
                },
                "required": ["date", "days"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "roll_to_business_day",
            "description": (
                "If the date is a weekend or holiday, move to the nearest business day "
                "in the given direction. A date that is already a business day is "
                "returned unchanged."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "ISO date or date-time"},
                    "direction": {"type": "string", "enum": ["forward", "backward"]},
                    "holidays": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "weekday",
            "description": "The day of the week a date falls on, e.g. 'Monday'.",
            "parameters": {
                "type": "object",
                "properties": {"date": {"type": "string", "description": "ISO date"}},
                "required": ["date"],
            },
        },
    },
]

TOOL_SCHEMA_V2: list[dict[str, Any]] = TOOL_SCHEMA_V1 + _BUSINESS_TOOLS

# Unversioned alias stays on V1 so run_h6_date_arm and every E67/E68 invocation
# keep the exact tool set their banked results were measured under.
TOOL_SCHEMA = TOOL_SCHEMA_V1

SCHEMAS = {"v1": TOOL_SCHEMA_V1, "v2": TOOL_SCHEMA_V2}

_DISPATCH = {
    "add_period": add_period,
    "last_day_of_month": last_day_of_month,
    "date_diff": date_diff,
    "add_business_days": add_business_days,
    "roll_to_business_day": roll_to_business_day,
    "weekday": weekday,
}


def dispatch(name: str, arguments: dict[str, Any]) -> str | int:
    """Execute a tool call by name. Raises on an unknown name or bad arguments."""
    fn = _DISPATCH.get(name)
    if fn is None:
        raise ValueError(
            f"unknown tool {name!r}. "
            f"hint: one of {sorted(_DISPATCH)}. This tool set counts dates only; "
            f"it has no domain helper that computes a legal deadline for you"
        )
    try:
        return fn(**arguments)
    except TypeError as exc:
        raise ValueError(
            f"bad arguments for {name}: {arguments!r} ({exc}). "
            f"hint: check the parameter names against the tool schema"
        ) from exc


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Deterministic date arithmetic for the H6 arm.",
        epilog="examples:\n"
        "  %(prog)s add --date 2026-01-31 --months 3          -> 2026-04-30\n"
        "  %(prog)s add --date 2026-04-03T14:30 --hours 72    -> 2026-04-06T14:30\n"
        "  %(prog)s last-day --date 2026-11-12                -> 2026-11-30\n"
        "  %(prog)s schema                                    -> the OpenAI tool schema",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="add a period to a date")
    a.add_argument("--date", required=True)
    for unit in ("years", "months", "days", "hours"):
        a.add_argument(f"--{unit}", type=int, default=0)

    ld = sub.add_parser("last-day", help="last calendar day of that month")
    ld.add_argument("--date", required=True)

    df = sub.add_parser("diff", help="whole days or hours between two dates")
    df.add_argument("--start", required=True)
    df.add_argument("--end", required=True)
    df.add_argument("--unit", default="days", choices=["days", "hours"])

    sub.add_parser("schema", help="print the OpenAI tool schema as JSON")

    args = ap.parse_args()
    if args.cmd == "add":
        print(add_period(args.date, args.years, args.months, args.days, args.hours))
    elif args.cmd == "last-day":
        print(last_day_of_month(args.date))
    elif args.cmd == "diff":
        print(date_diff(args.start, args.end, args.unit))
    else:
        print(json.dumps(TOOL_SCHEMA, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
