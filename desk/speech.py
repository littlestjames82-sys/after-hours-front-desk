"""Speech prep: rewrite a desk reply for the ear, not the eye.

The brain's reply is displayed verbatim in the transcript (and fed to the
extractor), but Sopro's model card is blunt: "Text frontend is minimal -
numbers/abbreviations/symbols may mispronounce (spell them out)." Handing
the synthesizer a raw hyphenated phone number gets it read as one long
number or mangled digits - the single most robotic moment of a v1 call.

This module only touches the copy that goes to the voice:
- phone numbers  -> digit words in human groups
  ("423-555-0147" -> "four two three, five five five, zero one four seven")
- dollar amounts -> words ("$89" -> "eighty-nine dollars")
Everything else passes through unchanged.
"""

import re

_DIGITS = ["zero", "one", "two", "three", "four",
           "five", "six", "seven", "eight", "nine"]
_ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven",
         "eight", "nine", "ten", "eleven", "twelve", "thirteen",
         "fourteen", "fifteen", "sixteen", "seventeen", "eighteen",
         "nineteen"]
_TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty",
         "seventy", "eighty", "ninety"]


def _under_1000(n: int) -> str:
    parts = []
    if n >= 100:
        parts.append(_ONES[n // 100] + " hundred")
        n %= 100
    if n >= 20:
        word = _TENS[n // 10]
        if n % 10:
            word += "-" + _ONES[n % 10]
        parts.append(word)
    elif n > 0 or not parts:
        parts.append(_ONES[n])
    return " ".join(parts)


def number_words(n: int) -> str:
    if n < 1000:
        return _under_1000(n)
    if n < 1_000_000:
        high, low = divmod(n, 1000)
        out = _under_1000(high) + " thousand"
        if low:
            out += " " + _under_1000(low)
        return out
    return str(n)  # beyond demo needs; digits read as-is


def _spoken_phone(digits: str) -> str:
    words = [_DIGITS[int(d)] for d in digits]
    if len(words) == 10:
        groups = [words[0:3], words[3:6], words[6:10]]
    elif len(words) == 7:
        groups = [words[0:3], words[3:7]]
    else:
        groups = [words]
    return ", ".join(" ".join(g) for g in groups)


_PHONE_RE = re.compile(
    r"\(?\d{3}\)?[\s.\-]\d{3}[\s.\-]\d{4}|\b\d{3}[\s.\-]\d{4}\b")
_MONEY_RE = re.compile(r"\$(\d[\d,]*)(?:\.(\d{2}))?")


def _money_sub(m: re.Match) -> str:
    dollars = int(m.group(1).replace(",", ""))
    cents = int(m.group(2) or 0)
    out = number_words(dollars) + (" dollar" if dollars == 1 else " dollars")
    if cents:
        out += f" and {number_words(cents)} cents"
    return out


# The brain writes typographic punctuation (curly quotes, en dashes);
# Sopro's minimal text frontend gets plain ASCII instead.
_ASCII = {"‘": "'", "’": "'", "“": '"', "”": '"',
          "–": "-", "—": "-", "…": "..."}


def prepare_for_speech(text: str) -> str:
    """Return the spoken copy of a reply (transcript keeps the original)."""
    for fancy, plain in _ASCII.items():
        text = text.replace(fancy, plain)
    text = text.replace(" & ", " and ")
    text = _PHONE_RE.sub(
        lambda m: _spoken_phone(re.sub(r"\D", "", m.group(0))), text)
    text = _MONEY_RE.sub(_money_sub, text)
    return text
