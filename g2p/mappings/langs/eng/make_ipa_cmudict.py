#!/usr/bin/env python

"""Convert CMUDict to IPA, removing stress markers. We can only handle
one pronunciation at a time so just take the first one."""

import fileinput
import json
import re

with open("eng_arpabet_to_ipa.json") as f:
    mappings = json.load(f)
    ipa_map = dict((e["in"], e["out"]) for e in mappings)

comment_re = re.compile(r"#.*$")
entry_re = re.compile(r"^(\S+?)(\(\d+\))?\s+(.*)$")
stress_re = re.compile(r"\d+$")
for spam in fileinput.input():
    m = entry_re.match(comment_re.sub("", spam.strip()))
    if m is None:
        continue
    word, alt, phones = m.groups()
    if alt is not None:  # skip alterantes
        continue
    phones = "".join(
        ipa_map[np] for np in (stress_re.sub("", p) for p in phones.split())
    )
    print("\t".join((word, phones)))
