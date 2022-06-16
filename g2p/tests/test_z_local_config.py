#!/usr/bin/env python3

"""
Test that the --config switch to g2p convert works

This test modifies the g2p database in memory, so it's important that it get
run last, in order to avoid changing the results of other unit test cases.

This file is also the right place to include other tests that make use of --config
to exercise different things.

We accomplish that in two ways:
 - in "./run.py dev", it gets appended after all the other tests, explicitly.
 - the file name has a "z" so it sorts last when "./run.py all" uses LOADER.discover()
"""

import json
import os
import tempfile
from pathlib import Path
from unittest import TestCase, main

from g2p.app import APP
from g2p.cli import convert, generate_mapping
from g2p.mappings.utils import normalize
from g2p.tests.public import PUBLIC_DIR


class LocalConfigTest(TestCase):
    def setUp(self):
        self.runner = APP.test_cli_runner()
        self.mappings_dir = Path(PUBLIC_DIR) / "mappings"

    def test_local_config(self):
        config_path = self.mappings_dir / "test.yaml"
        result = self.runner.invoke(
            convert,
            [
                "bbbb",
                "local-config-in",
                "local-config-out",
                "--config",
                config_path,
            ],
        )
        self.assertIn("aaaa", result.stdout)
        result = self.runner.invoke(
            convert,
            [
                "b",
                "local-config-in",
                "eng-ipa",
                "--config",
                config_path,
            ],
        )
        self.assertIn("ɑ", result.stdout)

    def test_case_insensitive_tokenizer(self):
        # Unit testing for https://github.com/ReadAlongs/Studio/issues/40
        # That issue was raised in Studio when the tokenizer was there, but
        # the tokenizer has been migrated to g2p since then, so the test and
        # fix belong here in g2p.

        # This test incidentally exercises passing --config a config file with
        # only one mapping in it, without the top-level "mappings:" list.
        tok_config = self.mappings_dir / "tokenize_punct_config.yaml"
        results = self.runner.invoke(
            convert, ["--tok", "--config", tok_config, "AAA-BBB", "tok-in", "tok-out"]
        )
        self.assertEqual(results.exit_code, 0)
        self.assertIn("aac_dbb", results.output)

        # While "AAA-BBB" gets tokenized as [word("AAA-BBB")], since "A-B" is
        # in the inventory, "D-C" gets tokenized as [word("D"), non-word("-"),
        # word("C")]. With rule D,d_end,,$, D will only become "d_end" if D is
        # at the end, which only occurs where we tokenize.
        results = self.runner.invoke(
            convert, ["--tok", "--config", tok_config, "D-C", "tok-in", "tok-out"]
        )
        self.assertEqual(results.exit_code, 0)
        self.assertIn("d_end-c", results.output)

    def test_null_mapping(self):
        """Empty lines in a mapping should just get ignored"""
        # Unit test case for bug fix: as of 2021-12-01, an empty rule would
        # cause the next rule to not get its match pattern created, and raise
        # an exception later. The null.csv mapping has such an empty rule,
        # which should get ignored, with the next rule, d->e, still working.
        null_config = self.mappings_dir / "null_config.yaml"
        results = self.runner.invoke(
            convert, ["--config", null_config, "x-ad-x", "null-in", "null-out"]
        )
        self.assertEqual(results.exit_code, 0)
        self.assertIn("x-be-x", results.output)

    def test_case_feeding_mapping(self):
        """Exercise the mapping using case to prevent feeding on in/out but not context"""
        case_feeding_config = self.mappings_dir / "case-feed" / "config.yaml"
        results = self.runner.invoke(
            convert,
            [
                "--config",
                case_feeding_config,
                "--tok",
                "ka-intinatin",
                "cf-in",
                "cf-out",
            ],
        )
        # print(results.output)
        self.assertEqual(results.exit_code, 0)
        self.assertIn("ke-antinetin", results.output)

    def test_missing_files(self):
        """Nice error messages when the mapping file or abbreviations file are missing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, "mapping-file-not-found.yaml")
            with open(config_file, "wt", encoding="utf8") as f:
                print("mapping: no-such-file.csv", file=f)
            results = self.runner.invoke(
                convert, ["--config", config_file, "a", "b", "c"]
            )
            self.assertNotEqual(results.exit_code, 0)
            self.assertIn(
                "Cannot load mapping data file", results.output + str(results.exception)
            )

        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, "abbrev-file-not-found.yaml")
            with open(os.path.join(tmpdir, "empty.csv"), "wt", encoding="utf8") as f:
                pass
            with open(config_file, "wt", encoding="utf8") as f:
                print("mapping: empty.csv", file=f)
                print("abbreviations: no-such-file.csv", file=f)
            results = self.runner.invoke(
                convert, ["--config", config_file, "a", "b", "c"]
            )
            self.assertNotEqual(results.exit_code, 0)
            self.assertIn(
                "Cannot load abbreviations data file",
                results.output + str(results.exception),
            )

    def test_generate_mapping(self):
        """Use a local config to test generate mapping with --from and --to"""
        # This test is rather hacky, because it relies on the fact that calling
        # g2p convert --config loads a config and keeps it in memory for the rest
        # of the unit tests. While that's a potential bug for testing g2p update,
        # and the very reason this file is called test_z_..., forcing it to be
        # called last, we're using it as a feature here.

        # It would be better to have a proper function to load in additional
        # mappings from a given config file, but right now that's not
        # implemented, and I don't want to make that a requirement for testing
        # "g2p generate-mapping --from/--to", so it'll have to wait.
        # TODO: write a internal load_from_config() function, or some such, and
        # factor out the repeated code to use it.

        # This first case has the side effect of loading gen-map_config.yaml
        config_path = self.mappings_dir / "gen-map_config.yaml"
        result = self.runner.invoke(
            convert, ["uyoesnmklbdt", "gm2", "gm2-ipa", "--config", config_path]
        )
        self.assertIn("uyɔɛsnmklbdt", result.stdout)
        # This second case confirms that gen-map_config.yaml is still loaded
        result = self.runner.invoke(convert, ["uyoesnmklbdt", "gm3a", "gm3-ipa"])
        self.assertIn("uyoesnmklbdt", result.stdout)

        # Now we do the real tests
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # for debugging:
            # output_dir = Path(".") / "gen-map-tests"
            # output_dir.mkdir(exist_ok=True)

            # 1 mapping in to 1 mapping out
            result = self.runner.invoke(
                generate_mapping,
                ["--from", "gm1", "--to", "gm2", "--out-dir", output_dir],
            )
            self.assertEqual(result.exit_code, 0)
            with open(self.mappings_dir / "gm1-ipa_to_gm2-ipa.json", "r") as f:
                ref = json.load(f)
            with open(output_dir / "gm1-ipa_to_gm2-ipa.json", "r") as f:
                output = json.load(f)
            self.assertEqual(output, ref)

            # 2 mappings in to 1 mapping out
            result = self.runner.invoke(
                generate_mapping,
                ["--from", "gm3", "--to", "gm2", "--out-dir", output_dir],
            )
            self.assertEqual(result.exit_code, 0)
            with open(self.mappings_dir / "gm3-ipa_to_gm2-ipa.json", "r") as f:
                ref = json.load(f)
            with open(output_dir / "gm3-ipa_to_gm2-ipa.json", "r") as f:
                output = json.load(f)
            self.assertEqual(output, ref)

            # 1 mapping in to 2 mappings out
            result = self.runner.invoke(
                generate_mapping,
                ["--from", "gm2", "--to", "gm3", "--out-dir", output_dir],
            )
            self.assertEqual(result.exit_code, 0)
            with open(self.mappings_dir / "gm2-ipa_to_gm3-ipa.json", "r") as f:
                ref = json.load(f)
            with open(output_dir / "gm2-ipa_to_gm3-ipa.json", "r") as f:
                output = json.load(f)
            self.assertEqual(output, ref)

    def test_compose_NFC_NFD(self):
        config_path = self.mappings_dir / "compose.yaml"
        result = self.runner.invoke(
            convert,
            [normalize("é", "NFD"), "c1", "c3", "--config", config_path, "-d", "-e"],
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn("[[(0, 0), (1, 0)], [(0, 0), (0, 1)]]", result.output)
        self.assertIn(
            "[[['e', 'ò'], ['́', 'ò']], [['ò', 'u'], ['ò', '̀']]]", result.output
        )

        result = self.runner.invoke(
            convert,
            [normalize("é", "NFC"), "c1", "c3", "--config", config_path, "-d", "-e"],
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn("[[(0, 0)], [(0, 0), (0, 1)]]", result.output)
        self.assertIn("[[['é', 'ò']], [['ò', 'u'], ['ò', '̀']]]", result.output)


if __name__ == "__main__":
    main()
