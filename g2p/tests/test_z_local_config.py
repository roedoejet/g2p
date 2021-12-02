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

from unittest import main, TestCase
import os

from g2p.app import APP
from g2p.cli import convert
from g2p.tests.public import PUBLIC_DIR


class LocalConfigTest(TestCase):
    def setUp(self):
        self.runner = APP.test_cli_runner()

    def test_local_config(self):
        config_path = os.path.join(PUBLIC_DIR, "mappings", "test.yaml")
        result = self.runner.invoke(
            convert,
            ["bbbb", "local-config-in", "local-config-out", "--config", config_path,],
        )
        self.assertIn("aaaa", result.stdout)
        result = self.runner.invoke(
            convert, ["b", "local-config-in", "eng-ipa", "--config", config_path,],
        )
        self.assertIn("ɑ", result.stdout)

    def test_case_insensitive_tokenizer(self):
        # Unit testing for https://github.com/ReadAlongs/Studio/issues/40
        # That issue was raised in Studio when the tokenizer was there, but
        # the tokenizer has been migrated to g2p since then, so the test and
        # fix belong here in g2p.

        # This test incidentally exercises passing --config a config file with
        # only one mapping in it, without the top-level "mappings:" list.
        tok_config = os.path.join(PUBLIC_DIR, "mappings", "tokenize_punct_config.yaml")
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
        null_config = os.path.join(PUBLIC_DIR, "mappings", "null_config.yaml")
        results = self.runner.invoke(
            convert, ["--config", null_config, "x-ad-x", "null-in", "null-out"]
        )
        self.assertEqual(results.exit_code, 0)
        self.assertIn("x-be-x", results.output)

    def test_case_feeding_mapping(self):
        """Exercise the mapping using case to prevent feeding on in/out but not context"""
        case_feeding_config = os.path.join(PUBLIC_DIR, "mappings", "case-feed", "config.yaml")
        results = self.runner.invoke(
            convert, ["--config", case_feeding_config, "--tok", "ka-intinatin", "cf-in", "cf-out"]
        )
        print(results.output)
        self.assertEqual(results.exit_code, 0)
        self.assertIn("ke-antinetin", results.output)


if __name__ == "__main__":
    main()
