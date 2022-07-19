#!/usr/bin/env python3

import re
from unittest import TestCase, main

from g2p.mappings import Mapping
from g2p.mappings.create_fallback_mapping import align_to_dummy_fallback


def rule(in_text, out_text, context_before, context_after, match_pattern):
    """Concise rule initializer for unit testing purposes only"""
    return {
        "in": in_text,
        "out": out_text,
        "context_before": context_before,
        "context_after": context_after,
        "match_pattern": re.compile(match_pattern),
    }


class FallbackTest(TestCase):
    """Basic Mapping Fallback Test.
    This feature is experimental, but it will try to map each character
    in a Mapping to one of the following 'unmarked' phonemes:
        ["ɑ", "i", "u", "t", "s", "n"]
    If the mapping is 'ipa', it will align the inventories directly.
    If not, it will take a best guess at what the Unicode character using Unidecode and then align from there.
    """

    def setUp(self):
        pass

    def test_mapping(self):
        mapping = Mapping(
            [
                {"in": "a", "out": "æ"},
                {"in": "e", "out": "ɐ"},
                {"in": "i", "out": "ɑ̃"},
                {"in": "b", "out": "β"},
                {"in": "g", "out": "ɡ"},
                {"in": "g", "out": "g"},
                {"in": "i", "out": "ةُ"},
            ],
            in_lang="test",
            out_lang="test-out",
        )
        ipa_mapping = Mapping(
            [
                {"in": "a", "out": "æ"},
                {"in": "e", "out": "ɐ"},
                {"in": "i", "out": "ɑ̃"},
                {"in": "b", "out": "β"},
                {"in": "g", "out": "ɡ"},
            ],
            in_lang="test",
            out_lang="test-ipa",
        )
        test_in = align_to_dummy_fallback(mapping)
        self.assertEqual(
            test_in.mapping,
            [
                rule("a", "ɑ", "", "", "a"),
                rule("e", "i", "", "", "e"),
                rule("i", "i", "", "", "i"),
                rule("b", "t", "", "", "b"),
                rule("g", "t", "", "", "g"),
                rule("g", "t", "", "", "g"),
                rule("i", "i", "", "", "i"),
            ],
        )

        test_out = align_to_dummy_fallback(mapping, "out")
        self.assertEqual(
            test_out.mapping,
            [
                rule("æ", "ɑi", "", "", "æ"),
                rule("ɐ", "ɑ", "", "", "ɐ"),
                rule("ɑ̃", "ɑ", "", "", "ɑ̃"),
                rule("β", "t", "", "", "β"),
                rule("ɡ", "t", "", "", "ɡ"),
                rule("g", "t", "", "", "g"),
                rule("ةُ", "ɑu", "", "", "ةُ"),
            ],
        )
        test_ipa = align_to_dummy_fallback(ipa_mapping, "out")
        self.assertEqual(
            test_ipa.mapping,
            [
                rule("æ", "ɑ", "", "", "æ"),
                rule("ɐ", "ɑ", "", "", "ɐ"),
                rule("ɑ̃", "ɑ", "", "", "ɑ̃"),
                rule("β", "s", "", "", "β"),
                rule("ɡ", "t", "", "", "ɡ"),
            ],
        )


if __name__ == "__main__":
    main()
