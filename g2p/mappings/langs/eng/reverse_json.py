#!/usr/bin/env python

import json

with open("eng_ipa_to_arpabet.json") as f:
    mappings = json.load(f)
    print("[")
    seen = set()
    for i, m in enumerate(mappings):
        if m["out"] in seen:
            continue
        seen.add(m["out"])
        if " " in m["out"]:
            continue
        print(
            '    { "in": "%s", "out": "%s" }%s'
            % (m["out"], m["in"], "," if i != len(mappings) - 1 else "")
        )
    print("]")
