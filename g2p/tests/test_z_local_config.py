#!/usr/bin/env python3

"""
Test that the --config switch to g2p convert works

This test modifies the g2p database in memory, so it's important that it get
run last, in order to avoid changing the results of other unit test cases.

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


if __name__ == "__main__":
    main()
