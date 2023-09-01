#!/usr/bin/env python

from unittest import TestCase, main

from g2p.mappings import Mapping, Rule
from g2p.mappings.create_fallback_mapping import align_to_dummy_fallback


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
        self.maxDiff = None
        mapping = Mapping(
            rules=[
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
            rules=[
                {"in": "a", "out": "æ"},
                {"in": "e", "out": "ɐ"},
                {"in": "i", "out": "ɑ̃"},
                {"in": "b", "out": "β"},
                {"in": "g", "out": "ɡ"},
            ],
            in_lang="test",
            out_lang="test-ipa",
        )
        test_in = align_to_dummy_fallback(mapping, quiet=True)
        self.assertEqual(
            test_in.rules,
            [
                Rule(in_char="a", out_char="ɑ", match_pattern="a"),
                Rule(in_char="e", out_char="i", match_pattern="e"),
                Rule(in_char="i", out_char="i", match_pattern="i"),
                Rule(in_char="b", out_char="t", match_pattern="b"),
                Rule(in_char="g", out_char="t", match_pattern="g"),
                Rule(in_char="g", out_char="t", match_pattern="g"),
                Rule(in_char="i", out_char="i", match_pattern="i"),
            ],
        )

        test_out = align_to_dummy_fallback(mapping, "out", quiet=True)
        self.assertEqual(
            test_out.rules,
            [
                Rule(in_char="æ", out_char="ɑi", match_pattern="æ"),
                Rule(in_char="ɐ", out_char="ɑ", match_pattern="ɐ"),
                Rule(in_char="ɑ̃", out_char="ɑ", match_pattern="ɑ̃"),
                Rule(in_char="β", out_char="t", match_pattern="β"),
                Rule(in_char="ɡ", out_char="t", match_pattern="ɡ"),
                Rule(in_char="g", out_char="t", match_pattern="g"),
                Rule(in_char="ةُ", out_char="ɑu", match_pattern="ةُ"),
            ],
        )
        test_ipa = align_to_dummy_fallback(ipa_mapping, "out", quiet=True)
        self.assertEqual(
            test_ipa.rules,
            [
                Rule(in_char="æ", out_char="ɑ", match_pattern="æ"),
                Rule(in_char="ɐ", out_char="ɑ", match_pattern="ɐ"),
                Rule(in_char="ɑ̃", out_char="ɑ", match_pattern="ɑ̃"),
                Rule(in_char="β", out_char="s", match_pattern="β"),
                Rule(in_char="ɡ", out_char="t", match_pattern="ɡ"),
            ],
        )


if __name__ == "__main__":
    main()
