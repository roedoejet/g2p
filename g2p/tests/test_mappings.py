#!/usr/bin/env python3

import io
import json
import os
import unicodedata as ud
from contextlib import redirect_stderr
from tempfile import NamedTemporaryFile
from typing import List
from unittest import TestCase, main

from g2p import exceptions
from g2p.mappings import Mapping
from g2p.tests.public import __file__ as public_data
from g2p.transducer import Transducer


def rules_from_strings(*mapping: str) -> List[dict]:
    """Quick pseudo constructor for unit testing of mappings"""
    rules = []
    for rule in mapping:
        key, value = rule.split(":")
        rules.append({"in": key, "out": value})
    return rules


class MappingTest(TestCase):
    """Basic Mapping Test"""

    def setUp(self):
        self.test_mapping_no_norm = Mapping(
            [
                {"in": "\u00e1", "out": "\u00e1"},
                {"in": "\u0061\u0301", "out": "\u0061\u0301"},
            ],
            norm_form="none",
        )
        self.test_mapping_norm = Mapping([{"in": "\u00e1", "out": "\u00e1"}])
        with open(
            os.path.join(os.path.dirname(public_data), "git_to_ipa.json"),
            encoding="utf8",
        ) as f:
            self.json_map = json.load(f)

    def test_normalization(self):
        self.assertEqual(
            ud.normalize("NFD", "\u00e1"), self.test_mapping_norm.mapping[0]["in"]
        )
        self.assertNotEqual(self.test_mapping_norm.mapping[0]["in"], "\u00e1")
        self.assertEqual(self.test_mapping_norm.mapping[0]["in"], "\u0061\u0301")
        self.assertEqual(self.test_mapping_no_norm.mapping[0]["in"], "\u00e1")
        self.assertEqual(self.test_mapping_no_norm.mapping[0]["out"], "\u00e1")
        self.assertEqual(self.test_mapping_no_norm.mapping[1]["in"], "\u0061\u0301")
        self.assertEqual(self.test_mapping_no_norm.mapping[1]["out"], "\u0061\u0301")

    def test_json_map(self):
        json_map = Mapping(
            self.json_map["map"],
            **{k: v for k, v in self.json_map.items() if k != "map"}
        )
        self.assertEqual(len(json_map), 34)
        self.assertTrue(json_map.kwargs["in_metadata"]["case_insensitive"])

    def test_as_is(self):
        """
        Test deprecated config: as_is.
        """

        # explicitly set as_is=False
        log_output = io.StringIO()
        with redirect_stderr(log_output):
            mapping_sorted = Mapping(
                [{"in": "a", "out": "b"}, {"in": "aa", "out": "c"}], as_is=False
            )
        self.assertTrue(mapping_sorted.wants_rules_sorted())
        self.assertIn(
            "deprecated",
            log_output.getvalue(),
            "it should warn that the feature is deprecated",
        )
        self.assertIn(
            "apply-longest-first",
            log_output.getvalue(),
            "it should show the equivalent rule_ordering setting",
        )

        # explicitly set as_is=True
        log_output = io.StringIO()
        with redirect_stderr(log_output):
            mapping = Mapping(
                [{"in": "a", "out": "b"}, {"in": "aa", "out": "c"}], as_is=True
            )
        self.assertFalse(mapping.wants_rules_sorted())
        self.assertIn(
            "deprecated",
            log_output.getvalue(),
            "it should warn that the feature is deprecated",
        )
        self.assertIn(
            "as-written",
            log_output.getvalue(),
            "it should show the equivalent rule_ordering setting",
        )

        # test the default (rule_ordering="as-written")
        mapping_as_is = Mapping([{"in": "a", "out": "b"}, {"in": "aa", "out": "c"}])
        self.assertFalse(mapping.wants_rules_sorted())

        # test the alternative (rule_ordering="apply-longest-first")
        transducer = Transducer(mapping_sorted)
        transducer_as_is = Transducer(mapping_as_is)
        self.assertEqual(transducer("aa").output_string, "c")
        self.assertEqual(transducer_as_is("aa").output_string, "bb")

    def test_rule_ordering(self):
        """
        Test the config option:

        rule-ordering: 'as-written' (default)

        or

        rule-ordering: 'apply-shortest-first'
        """
        rules = [{"in": "a", "out": "b"}, {"in": "aa", "out": "c"}]

        transducer_longest_first = Transducer(
            Mapping(rules, rule_ordering="apply-longest-first")
        )
        self.assertEqual(transducer_longest_first("aa").output_string, "c")

        transducer_as_written = Transducer(Mapping(rules, rule_ordering="as-written"))
        self.assertEqual(transducer_as_written("aa").output_string, "bb")

        transducer_default = Transducer(Mapping(rules))
        self.assertEqual(transducer_default("aa").output_string, "bb")

    def test_rule_ordering_given_invalid_value(self):
        """
        It should log an error messages if given an invalid value for
        rule_ordering=...
        """
        rules = [{"in": "a", "out": "b"}, {"in": "aa", "out": "c"}]

        # typo in the valid setting:
        incorrect_value = "apply-longest-frist"
        correct_value = "apply-longest-first"

        log_output = io.StringIO()
        with redirect_stderr(log_output):
            Mapping(rules, rule_ordering=incorrect_value)

        self.assertIn(incorrect_value, log_output.getvalue())
        self.assertIn(correct_value, log_output.getvalue())

    def test_case_sensitive(self):
        mapping = Mapping([{"in": "A", "out": "b"}], case_sensitive=False)
        mapping_case_sensitive = Mapping([{"in": "A", "out": "b"}])
        transducer = Transducer(mapping)
        transducer_case_sensitive = Transducer(mapping_case_sensitive)
        self.assertEqual(transducer("a").output_string, "b")
        self.assertEqual(transducer_case_sensitive("a").output_string, "a")
        self.assertEqual(transducer("A").output_string, "b")

    def test_escape_special(self):
        mapping = Mapping([{"in": r"\d", "out": "digit"}])
        mapping_escaped = Mapping([{"in": r"\d", "out": "b"}], escape_special=True)
        transducer = Transducer(mapping)
        transducer_escaped = Transducer(mapping_escaped)
        self.assertEqual(transducer("1").output_string, "digit")
        self.assertEqual(transducer(r"\d").output_string, r"\d")
        self.assertEqual(transducer_escaped("1").output_string, "1")
        self.assertEqual(transducer_escaped(r"\d").output_string, "b")

    def test_norm_form(self):
        mapping_nfc = Mapping([{"in": "a\u0301", "out": "a"}])  # Defaults to NFC
        mapping_nfd = Mapping([{"in": "a\u0301", "out": "a"}], norm_form="NFD")
        mapping_none = Mapping([{"in": "a\u0301", "out": "a"}], norm_form=False)

        transducer_nfc = Transducer(mapping_nfc)
        transducer_nfd = Transducer(mapping_nfd)
        transducer_none = Transducer(mapping_none)

        self.assertEqual(transducer_nfc("a\u0301").output_string, "a")
        self.assertEqual(transducer_nfc("\u00E1").output_string, "a")
        self.assertEqual(transducer_nfd("a\u0301").output_string, "a")
        self.assertEqual(transducer_nfd("\u00E1").output_string, "a")
        self.assertEqual(transducer_none("a\u0301").output_string, "a")
        self.assertEqual(transducer_none("\u00E1").output_string, "\u00E1")

    def test_reverse(self):
        mapping = Mapping([{"in": "a", "out": "b"}])
        mapping_reversed = Mapping([{"in": "a", "out": "b"}], reverse=True)
        transducer = Transducer(mapping)
        transducer_reversed = Transducer(mapping_reversed)
        self.assertEqual(transducer("a").output_string, "b")
        self.assertEqual(transducer("b").output_string, "b")
        self.assertEqual(transducer_reversed("a").output_string, "a")
        self.assertEqual(transducer_reversed("b").output_string, "a")

    def test_minimal(self):
        mapping = Mapping(
            os.path.join(
                os.path.dirname(public_data), "mappings", "minimal_config.yaml"
            )
        )
        transducer = Transducer(mapping)
        self.assertEqual(transducer("abb").output_string, "aaa")
        self.assertEqual(transducer("a").output_string, "a")
        self.assertFalse(mapping.wants_rules_sorted())
        self.assertFalse(mapping.kwargs["case_sensitive"])
        self.assertTrue(mapping.kwargs["escape_special"])
        self.assertEqual(mapping.kwargs["norm_form"], "NFD")
        self.assertTrue(mapping.kwargs["reverse"])

    def test_abbreviations(self):
        mapping = Mapping(
            os.path.join(
                os.path.dirname(public_data), "mappings", "abbreviation_config.yaml"
            )
        )
        self.assertEqual(mapping.mapping[0]["in"], "i|u")
        self.assertEqual(mapping.mapping[1]["in"], "a|e|i|o|u")
        transducer = Transducer(mapping)
        self.assertEqual(transducer("i").output_string, "1")
        self.assertEqual(transducer("e").output_string, "2")

    def test_rule_ordering_from_config(self):
        """
        Same as test_minimal, but uses "rule-ordering" instead of "as-is" in the config.
        """
        mapping = Mapping(
            os.path.join(os.path.dirname(public_data), "mappings", "rule-ordering.yaml")
        )
        transducer = Transducer(mapping)
        self.assertEqual(transducer("abb").output_string, "aaa")
        self.assertEqual(transducer("a").output_string, "a")
        self.assertTrue(mapping.wants_rules_sorted())
        self.assertEqual(mapping.kwargs["rule_ordering"], "apply-longest-first")
        self.assertFalse(mapping.kwargs["case_sensitive"])
        self.assertTrue(mapping.kwargs["escape_special"])
        self.assertEqual(mapping.kwargs["norm_form"], "NFD")
        self.assertTrue(mapping.kwargs["reverse"])

    def test_null_input(self):
        mapping = Mapping([{"in": "", "out": "a"}])
        self.assertFalse(mapping())

    def test_no_escape(self):
        mapping = Mapping(
            os.path.join(os.path.dirname(public_data), "mappings", "no_escape.csv")
        )
        transducer = Transducer(mapping)
        self.assertEqual(transducer("?").output_string, "ʔ")

    def test_invalid_rules_json(self):
        rules = [{"in": "a"}, {"out": "c"}]
        self.assertRaises(exceptions.MalformedMapping, Mapping, rules)

    def test_invalid_rules_csv(self):
        tf = NamedTemporaryFile(
            prefix="test_invalid_rules_", mode="w", suffix=".csv", delete=False
        )
        tf.write("good-in,good-out\n\ngood-in-no-out\n")
        tf.close()
        self.assertRaises(exceptions.MalformedMapping, Mapping, tf.name)
        os.unlink(tf.name)

    def test_invalid_rules_filetype(self):
        tf = NamedTemporaryFile(
            prefix="test_invalid_rules_", mode="w", suffix=".foo", delete=False
        )
        tf.write("good-in,good-out\n\ngood-in-no-out\n")
        tf.close()
        self.assertRaises(exceptions.IncorrectFileType, Mapping, tf.name)
        os.unlink(tf.name)

    def test_extend_and_deduplicate(self):
        mapping1 = Mapping(rules_from_strings("a:b", "c:d", "g:h"))
        mapping2 = Mapping(rules_from_strings("a:x", "c:d", "e:f"))
        extend_ref = Mapping(
            rules_from_strings("a:b", "c:d", "g:h", "a:x", "c:d", "e:f")
        )
        mapping1.extend(mapping2)
        self.assertEquals(mapping1.mapping, extend_ref.mapping)
        dedup_ref = Mapping(rules_from_strings("a:b", "c:d", "g:h", "a:x", "e:f"))
        mapping1.deduplicate()
        self.assertEquals(mapping1.mapping, dedup_ref.mapping)

    def test_g2p_studio_csv(self):
        # Ensure that a single CSV file from Studio works properly
        mapping = Mapping(
            os.path.join(os.path.dirname(public_data), "mappings", "g2p_studio.csv")
        )
        transducer = Transducer(mapping)
        self.assertEqual(
            transducer("Jouni haluaa juoda kahvia").output_string,
            "Jouni hɑluɑː juodɑ kɑhviɑ",
        )
        # Concatenate them (this is not a good idea) and make sure it works anyway
        tf = NamedTemporaryFile(
            prefix="test_g2p_g2p_",
            mode="w",
            suffix=".csv",
            delete=False,
            encoding="utf8",
        )
        with open(
            os.path.join(os.path.dirname(public_data), "mappings", "g2p_studio.csv"),
            encoding="utf8",
        ) as fh:
            tf.write(fh.read())
        # In fact you can't concatenate them anyway. They don't end in newline.
        tf.write("\n")
        with open(
            os.path.join(os.path.dirname(public_data), "mappings", "g2p_studio2.csv"),
            encoding="utf8",
        ) as fh:
            tf.write(fh.read())
        tf.close()
        mapping = Mapping(tf.name)
        transducer = Transducer(mapping)
        self.assertEqual(
            transducer("tee on herkullista").output_string, "teː on herkullistɑ"
        )
        os.unlink(tf.name)


if __name__ == "__main__":
    main()
