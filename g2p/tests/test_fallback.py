#!/usr/bin/env python3

from unittest import main, TestCase
import re
from g2p.mappings import Mapping
from g2p.mappings.create_fallback_mapping import align_to_dummy_fallback
from g2p.tests.public import __file__ as public_data


class FallbackTest(TestCase):
    ''' Basic Mapping Fallback Test.
        This feature is experimental, but it will try to map each character
        in a Mapping to one of the following 'unmarked' phonemes:
            ["ɑ", "i", "u", "t", "s", "n"]
        If the mapping is 'ipa', it will align the inventories directly.
        If not, it will take a best guess at what the Unicode character using Unidecode and then align from there.
    '''

    def setUp(self):
        pass

    def test_mapping(self):
        mapping = Mapping([{'in': 'a', 'out': 'æ'},
                           {'in': 'e', 'out': 'ɐ'},
                           {'in': 'i', 'out': 'ɑ̃'},
                           {'in': 'b', 'out': 'β'},
                           {'in': 'g', 'out': 'ɡ'},
                           {'in': 'g', 'out': 'g'},
                           {'in': 'i', 'out': 'ةُ'}], in_lang='test', out_lang='test-out')
        ipa_mapping = Mapping([{'in': 'a', 'out': 'æ'},
                               {'in': 'e', 'out': 'ɐ'},
                               {'in': 'i', 'out': 'ɑ̃'},
                               {'in': 'b', 'out': 'β'},
                               {'in': 'g', 'out': 'ɡ'}], in_lang='test', out_lang='test-ipa')
        test_in = align_to_dummy_fallback(mapping)
        self.assertEqual(test_in.mapping, [{'in': 'a', 'out': 'ɑ', 'context_before': '', 'context_after': '', 'match_pattern': re.compile('a')}, {'in': 'e', 'out': 'i', 'context_before': '', 'context_after': '', 'match_pattern': re.compile('e')}, {'in': 'i', 'out': 'i', 'context_before': '', 'context_after': '', 'match_pattern': re.compile('i')}, {'in': 'b', 'out': 't', 'context_before': '',
                                                                                                                                                                                                                                                                                                                                                              'context_after': '', 'match_pattern': re.compile('b')}, {'in': 'g', 'out': 't', 'context_before': '', 'context_after': '', 'match_pattern': re.compile('g')}, {'in': 'g', 'out': 't', 'context_before': '', 'context_after': '', 'match_pattern': re.compile('g')}, {'in': 'i', 'out': 'i', 'context_before': '', 'context_after': '', 'match_pattern': re.compile('i')}])
        test_out = align_to_dummy_fallback(mapping, 'out')
        self.assertEqual(test_out.mapping, [{'in': 'æ', 'out': 'ɑi', 'context_before': '', 'context_after': '', 'match_pattern': re.compile('æ')}, {'in': 'ɐ', 'out': 'ɑ', 'context_before': '', 'context_after': '', 'match_pattern': re.compile('ɐ')}, {'in': 'ɑ̃', 'out': 'ɑ', 'context_before': '', 'context_after': '', 'match_pattern': re.compile('ɑ̃')}, {
                         'in': 'β', 'out': 't', 'context_before': '', 'context_after': '', 'match_pattern': re.compile('β')}, {'in': 'ɡ', 'out': 't', 'context_before': '', 'context_after': '', 'match_pattern': re.compile('ɡ')}, {'in': 'g', 'out': 't', 'context_before': '', 'context_after': '', 'match_pattern': re.compile('g')}, {'in': 'ةُ', 'out': 'ɑu', 'context_before': '', 'context_after': '', 'match_pattern': re.compile('ةُ')}])
        test_ipa = align_to_dummy_fallback(ipa_mapping, 'out')
        self.assertEqual(
            test_ipa.mapping,
            [{'in': 'æ', 'out': 'ɑ', 'context_before': '', 'context_after': '', 'match_pattern': re.compile('æ')},
             {'in': 'ɐ', 'out': 'ɑ', 'context_before': '', 'context_after': '', 'match_pattern': re.compile('ɐ')},
             {'in': 'ɑ̃', 'out': 'ɑ', 'context_before': '', 'context_after': '', 'match_pattern': re.compile('ɑ̃')},
             {'in': 'β', 'out': 's', 'context_before': '', 'context_after': '', 'match_pattern': re.compile('β')},
             {'in': 'ɡ', 'out': 't', 'context_before': '', 'context_after': '', 'match_pattern': re.compile('ɡ')}])
if __name__ == "__main__":
    main()
