#!/usr/bin/env python

"""Convert CMUDict to IPA. We can only handle one pronunciation at a time so just take the first one."""

import json
import re

with open("eng_arpabet_to_ipa.json") as f:
    mappings = json.load(f)
    ipa_map = dict((e["in"], e["out"]) for e in mappings)

entry_re = re.compile(r"^(\S+?)(\(\d+\))?\s+(.*)$")
with open("cmudict_SPHINX_40.txt") as f:
    for spam in f:
        m = entry_re.match(spam.strip())
        if m is None:
            continue
        if m.group(2) is not None:  # skip alterantes
            continue
        phones = "".join(ipa_map[p] for p in m.group(3).split())
        print("\t".join((m.group(1), phones)))
