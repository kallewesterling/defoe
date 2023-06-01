import re


class DotDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


DATE = re.compile(
    r"(1[6-9]\d{2}(-|/)(0[1-9]|1[0-2])(-|/)(0[1-9]|[12]\d|3[01]))"
)

DATE_LONG = re.compile(r"(1[6-9]\d\d)")

DATE_SHORT = re.compile(r"\d\d")

DATE_PATTERNS = DotDict(dict(standard=DATE, long=DATE_LONG, short=DATE_SHORT))

PART_ID = re.compile(r"[^A-Za-z0-9]+")
