#!/usr/bin/env python3

""" Test Mapping utility functions
"""

import os
from collections import defaultdict
from unittest import TestCase, main

import yaml

from g2p.exceptions import IncorrectFileType, MalformedMapping, RecursionError
from g2p.mappings import Mapping, utils
from g2p.tests.public import PUBLIC_DIR


class UtilsTest(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        gen_mapping = os.path.join(PUBLIC_DIR, "mappings", "test_to_test-out.json")
        gen_config = os.path.join(PUBLIC_DIR, "mappings", "test_config.yaml")
        if os.path.exists(gen_config):
            os.remove(gen_config)
        if os.path.exists(gen_mapping):
            os.remove(gen_mapping)
        fresh_config = {"language_name": "generated", "mappings": []}
        with open(os.path.join(PUBLIC_DIR, "mappings", "generated_add.yaml"), "w") as f:
            yaml.dump(
                fresh_config, f, Dumper=utils.IndentDumper, default_flow_style=False
            )

    def test_abb_expand(self):
        test_dict = defaultdict(list)
        bad_dict = defaultdict(list)
        test_dict["VOWELS"].extend(["HIGH_VOWELS", "e", "o"])
        test_dict["HIGH_VOWELS"].extend(["i", "u"])
        bad_dict["VOWELS"].extend(["HIGH_VOWELS", "e", "o"])
        bad_dict["HIGH_VOWELS"].extend(
            ["HIGH_VOWELS", "u"]
        )  # shouldn't allow self-referential abbreviations
        expanded_plain = utils.expand_abbreviations("test", test_dict)
        expanded_bad_plain = utils.expand_abbreviations("test", bad_dict)
        with self.assertRaises(RecursionError):
            utils.expand_abbreviations("HIGH_VOWELS", bad_dict)
        expanded_non_recursive = utils.expand_abbreviations("HIGH_VOWELS", test_dict)
        expanded_recursive = utils.expand_abbreviations("VOWELS", test_dict)
        self.assertEqual("test", expanded_plain)
        self.assertEqual("test", expanded_bad_plain)
        self.assertEqual("i|u", expanded_non_recursive)
        self.assertEqual("i|u|e|o", expanded_recursive)

    def test_abb_flatten_and_expand_format(self):
        test_rows = [["VOWEL", "a", "e", "i", "o", "u"], ["OTHER", "t", "e", "s", "t"]]
        default_dict = defaultdict(list)
        default_dict["VOWEL"].extend(["a", "e", "i", "o", "u"])
        default_dict["OTHER"].extend(["t", "e", "s", "t"])
        empty_rows = []
        while len(empty_rows) < 10:
            empty_rows.append(["", "", "", "", "", ""])
        self.assertEqual(utils.flatten_abbreviations_format(test_rows), default_dict)
        self.assertEqual(utils.expand_abbreviations_format(default_dict), test_rows)
        self.assertEqual(utils.expand_abbreviations_format({}), empty_rows)

    def test_unicode_escape(self):
        """Should turn \u0331 declared in CSVs
        into actual Unicode string for that codepoint
        """
        self.assertEqual("\u0000", utils.unicode_escape("\\u0000"))
        self.assertEqual("\u0331", utils.unicode_escape("\\u0331"))
        self.assertEqual("\u26F0", utils.unicode_escape("\\u26F0"))

    def test_fixed_width(self):
        # TODO: Test utils.create_fixed_width_lookbehind and utils.pattern_to_fixed_width_lookbehinds
        pass

    def test_pattern(self):
        pass

    def test_load_mapping(self):
        with self.assertRaises(MalformedMapping):
            utils.load_mapping_from_path(
                os.path.join(PUBLIC_DIR, "mappings", "malformed_config.yaml")
            )
        minimal = utils.load_mapping_from_path(
            os.path.join(PUBLIC_DIR, "mappings", "minimal_config.yaml")
        )
        csv = utils.load_mapping_from_path(
            os.path.join(PUBLIC_DIR, "mappings", "minimal_configs.yaml"), 0
        )
        tsv = utils.load_mapping_from_path(
            os.path.join(PUBLIC_DIR, "mappings", "minimal_configs.yaml"), 1
        )
        psv = utils.load_mapping_from_path(
            os.path.join(PUBLIC_DIR, "mappings", "minimal_configs.yaml"), 2
        )
        json = utils.load_mapping_from_path(
            os.path.join(PUBLIC_DIR, "mappings", "minimal_configs.yaml"), 3
        )
        xlsx = utils.load_mapping_from_path(
            os.path.join(PUBLIC_DIR, "mappings", "minimal_configs.yaml"), 4
        )
        self.assertEqual(minimal["mapping_data"], csv["mapping_data"])
        self.assertEqual(minimal["mapping_data"], tsv["mapping_data"])
        self.assertEqual(minimal["mapping_data"], psv["mapping_data"])
        self.assertEqual(minimal["mapping_data"], json["mapping_data"])
        self.assertEqual(minimal["mapping_data"], xlsx["mapping_data"])

    def test_validate(self):
        pass

    def test_escape_special(self):
        self.assertEqual(utils.escape_special_characters({"in": "?"}), {"in": "\?"})

    def test_load_abbs(self):
        with self.assertRaises(IncorrectFileType):
            utils.load_abbreviations_from_file(
                os.path.join(PUBLIC_DIR, "mappings", "abbreviations.json")
            )
        for abb in ["abbreviations.csv", "abbreviations.tsv", "abbreviations.psv"]:
            abbs = utils.load_abbreviations_from_file(
                os.path.join(PUBLIC_DIR, "mappings", abb)
            )
            self.assertTrue("VOWEL" in abbs)
            self.assertEqual(abbs["VOWEL"], ["a", "e", "i", "o", "u"])

    def test_generated_mapping(self):
        config = {
            "in_lang": "test",
            "out_lang": "test-out",
            "rule_ordering": "apply-longest-first",
        }
        # config = utils.generate_config('test', 'test-out', 'Test', 'TestOut')
        config["mapping"] = [{"in": "a", "out": "b"}]
        mapping = Mapping(**config)
        mapping.config_to_file(os.path.join(PUBLIC_DIR, "mappings", "test_config.yaml"))
        mapping.config_to_file(
            os.path.join(PUBLIC_DIR, "mappings", "generated_add.yaml")
        )
        mapping.mapping_to_file(os.path.join(PUBLIC_DIR, "mappings"))
        test_config = utils.load_mapping_from_path(
            os.path.join(PUBLIC_DIR, "mappings", "test_config.yaml")
        )
        test_config_added = utils.load_mapping_from_path(
            os.path.join(PUBLIC_DIR, "mappings", "generated_add.yaml")
        )
        self.assertEqual(
            test_config["mapping_data"],
            [{"in": "a", "out": "b", "context_before": "", "context_after": ""}],
        )
        self.assertEqual(test_config["in_lang"], "test")
        self.assertEqual(test_config["out_lang"], "test-out")
        self.assertEqual(test_config["language_name"], "test")
        self.assertEqual(test_config["display_name"], "test custom to test-out custom")
        self.assertEqual(
            test_config_added["mapping_data"],
            [{"in": "a", "out": "b", "context_before": "", "context_after": ""}],
        )
        self.assertEqual(test_config_added["in_lang"], "test")
        self.assertEqual(test_config_added["out_lang"], "test-out")
        self.assertEqual(test_config_added["language_name"], "test")
        self.assertEqual(
            test_config_added["display_name"], "test custom to test-out custom"
        )

    def test_normalize_to_NFD_with_indices(self):
        # Usefull site to get combining character code points:
        # http://www.alanwood.net/unicode/combining_diacritical_marks.html
        e_acute_nfd = "e\u0301"
        self.assertEqual(
            utils.normalize_with_indices("é", "NFD"),
            (e_acute_nfd, [(0, 0), (0, 1)]),
        )
        o_graveabove_nfd = "o\u0300"
        self.assertEqual(
            utils.normalize_with_indices("ò", "NFD"),
            (o_graveabove_nfd, [(0, 0), (0, 1)]),
        )
        o_graveabove_acutebelow_mixed = "ò\u0317"
        o_graveabove_acutebelow_nfd = "o\u0300\u0317"
        self.assertEqual(
            utils.normalize_with_indices(o_graveabove_acutebelow_mixed, "NFD"),
            (o_graveabove_acutebelow_nfd, [(0, 0), (0, 1), (1, 2)]),
        )
        # From https://en.wikipedia.org/wiki/Precomposed_character:
        # "\u1e53" (ṓ) == "\u014d\u0301" (ṓ) == "\u006f\u0304\u0301" (ṓ)
        self.assertEqual(
            utils.normalize_with_indices("\u1e53", "NFD"),
            ("\u006f\u0304\u0301", [(0, 0), (0, 1), (0, 2)]),
        )
        self.assertEqual(
            utils.normalize_with_indices("\u014d\u0301", "NFD"),
            ("\u006f\u0304\u0301", [(0, 0), (0, 1), (1, 2)]),
        )

    def test_compose_indices(self):
        self.assertEqual(
            utils.compose_indices([(0, 1), (1, 4)], [(0, 0), (1, 2), (1, 3), (4, 2)]),
            [(0, 2), (0, 3), (1, 2)],
        )
        self.assertEqual(
            utils.compose_indices([(0, 0), (0, 1), (1, 2)], [(0, 3), (1, 3), (2, 3)]),
            [(0, 3), (1, 3)],
        )
        self.assertEqual(
            utils.compose_indices([(0, 1), (1, 2)], [(1, 4), (3, 1)]),
            [(0, 4)],
        )

    def test_normalize_to_NFC_with_indices(self):
        self.assertEqual(
            utils.normalize_with_indices("e\u0301", "NFC"),
            ("é", [(0, 0), (1, 0)]),
        )
        self.assertEqual(
            utils.normalize_with_indices("ò\u0317", "NFC"),
            ("ò̗", [(0, 0), (1, 1)]),
        )
        self.assertEqual(
            utils.normalize_with_indices("\u014d\u0301", "NFC"),
            ("\u1e53", [(0, 0), (1, 0)]),
        )
        self.assertEqual(
            utils.normalize_with_indices("o\u0304\u0301", "NFC"),
            ("\u1e53", [(0, 0), (1, 0), (2, 0)]),
        )
        self.assertEqual(
            utils.normalize_with_indices("\u014d\u0301", "none"),
            ("\u014d\u0301", [(0, 0), (1, 1)]),
        )

    def test_normalize_to_NFK_with_indices(self):
        e_acute_nfd = "e\u0301"
        self.assertEqual(
            utils.normalize_with_indices(e_acute_nfd, "NFKC"),
            ("é", [(0, 0), (1, 0)]),
        )
        self.assertEqual(
            utils.normalize_with_indices("é", "NFKD"),
            (e_acute_nfd, [(0, 0), (0, 1)]),
        )


if __name__ == "__main__":
    main()
