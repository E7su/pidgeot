# -*- coding: utf-8 -*-

from fuzzywuzzy import fuzz


def fuzzeq(str1, str2):
    return fuzz.ratio(str1.lower(), str2.lower()) > 80


def equals(txt, pattern):
    if not txt and not pattern:
        return True

    if not txt:
        return False

    if not pattern:
        return False

    return any([fuzzeq(txt, p.strip()) for p in pattern.split(u"|")])


def is_command(txt, pattern):
    if not txt:
        return False

    if not pattern:
        return False

    txt = txt.lower()

    return any([txt.startswith(p.lower()) for p in pattern.split(u"|")])
