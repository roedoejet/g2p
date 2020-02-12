from unittest import main, TestCase
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
        self.assertEqual(test_in[1], [{'in': 'a', 'out': 'ɑ'}, {'in': 'e', 'out': 'i'}, {'in': 'i', 'out': 'i'}, {
                         'in': 'b', 'out': 't'}, {'in': 'g', 'out': 't'}, {'in': 'g', 'out': 't'}, {'in': 'i', 'out': 'i'}])
        test_out = align_to_dummy_fallback(mapping, 'out')
        self.assertEqual(test_out[1], [{'in': 'æ', 'out': 'ɑi'}, {'in': 'ɐ', 'out': 'ɑ'}, {'in': 'ɑ̃', 'out': 'ɑ'}, {
                         'in': 'β', 'out': 't'}, {'in': 'ɡ', 'out': 't'}, {'in': 'g', 'out': 't'}, {'in': 'ةُ', 'out': 'ɑu'}])
        test_ipa = align_to_dummy_fallback(ipa_mapping, 'out')
        self.assertEqual(test_ipa[1], [{'in': 'æ', 'out': 'ɑ'}, {'in': 'ɐ', 'out': 'ɑ'}, {
                         'in': 'ɑ̃', 'out': 'ɑ'}, {'in': 'ɡ', 'out': 't'}, {'in': 'β', 'out': 's'}])


if __name__ == "__main__":
    main()
