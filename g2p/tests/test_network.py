#!/usr/bin/env python

from unittest import TestCase, main

from g2p import make_g2p
from g2p.exceptions import InvalidLanguageCode, NoPath
from g2p.log import LOGGER
from g2p.transducer import CompositeTransducer, Transducer


class NetworkTest(TestCase):
    """Basic Test for available networks"""

    def setUp(self):
        pass

    def test_not_found(self):
        with self.assertRaises(InvalidLanguageCode):
            with self.assertLogs(LOGGER, level="ERROR"):
                make_g2p("foo", "eng-ipa")
        with self.assertRaises(InvalidLanguageCode):
            with self.assertLogs(LOGGER, level="ERROR"):
                make_g2p("git", "bar")

    def test_no_path(self):
        with self.assertRaises(NoPath), self.assertLogs(LOGGER, level="ERROR"):
            make_g2p("hei", "git")

    def test_valid_composite(self):
        transducer = make_g2p("atj", "eng-ipa", tokenize=False)
        self.assertTrue(isinstance(transducer, CompositeTransducer))
        self.assertEqual("niɡiɡw", transducer("nikikw").output_string)

    def test_valid_transducer(self):
        transducer = make_g2p("atj", "atj-ipa", tokenize=False)
        self.assertTrue(isinstance(transducer, Transducer))
        self.assertEqual("niɡiɡw", transducer("nikikw").output_string)


if __name__ == "__main__":
    main()
