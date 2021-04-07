#!/usr/bin/env python3

""" Test Mapping langs utility functions
"""

from unittest import TestCase, main

from g2p.mappings.langs import utils


class LangsUtilsTest(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_is_IPA(self):
        self.assertTrue(utils.is_panphon("ijŋeːʒoːɡd͡ʒ"))  # All panphon chars
        self.assertTrue(utils.is_panphon("ij ij"))  # tokenizes on spaces
        # ASCII g is not ipa/panphon use ɡ (\u0261)
        self.assertFalse(utils.is_panphon("ga"))
        # ASCII : is not ipa/panphon, use ː (\u02D0)
        self.assertFalse(utils.is_panphon("e:"))

    def test_is_arpabet(self):
        arpabet_string = "S AH S IY  EH  AO N  T EH"
        non_arpabet_string = "sometext"
        self.assertTrue(utils.is_arpabet(arpabet_string))
        self.assertFalse(utils.is_arpabet(non_arpabet_string))


if __name__ == "__main__":
    main()
