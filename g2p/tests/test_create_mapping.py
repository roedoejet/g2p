"""
Test all Mappings
"""

from unittest import main, TestCase

from g2p.mappings import Mapping
from g2p.mappings.create_ipa_mapping import create_mapping
from g2p.transducer import Transducer


def make_map_dict(mapping):
    return dict((m['in'], m['out']) for m in mapping['map'])


class MappingCreationTest(TestCase):
    def setUp(self):
        self.mappings = [
            {"in": "ɑ",	"out": "AA"},
            {"in": "eː",	"out": "EY"},
            {"in": "i",	"out": "IY"},
            {"in": "u",	"out": "UW"},
            {"in": "tʃ",	"out": "CH"},
            {"in": "p",	"out": "P"},
            {"in": "t",	"out": "T"},
            {"in": "k",	"out": "K"},
            {"in": "w",	"out": "W"},
        ]
        self.target_mapping = Mapping(
            self.mappings, in_lang='eng-ipa', out_lang='eng-arpabet', out_delimiter=' ')

    def test_unigram_mappings(self):
        src_mappings = [
            {"in": "ᐃ", "out": "i"},
            {"in": "ᐅ", "out": "u"},
            {"in": "ᐊ", "out": "a"},
        ]
        src_mapping = Mapping(src_mappings, in_lang='crj', out_lang='crj-ipa')
        mapping = create_mapping(src_mapping, self.target_mapping)
        transducer = Transducer(mapping)
        self.assertEqual(transducer('a'), 'ɑ')
        self.assertEqual(transducer('i'), 'i')
        self.assertEqual(transducer('u'), 'u')

    def test_bigram_mappings(self):
        src_mappings = [
            {"in": "ᐱ", "out": "pi"},
            {"in": "ᑎ", "out": "ti"},
            {"in": "ᑭ", "out": "ki"},
        ]
        src_mapping = Mapping(src_mappings, in_lang='crj', out_lang='crj-ipa')
        mapping = create_mapping(src_mapping, self.target_mapping)
        transducer = Transducer(mapping)
        self.assertEqual(transducer('pi'), 'pi')
        self.assertEqual(transducer('ti'), 'ti')
        self.assertEqual(transducer('ki'), 'ki')

    def test_trigram_mappings(self):
        src_mappings = [
            {"in": "ᒋ", "out": "t͡ʃi"},
            {"in": "ᒍ", "out": "t͡ʃu"},
            {"in": "ᒐ", "out": "t͡ʃa"},
        ]
        src_mapping = Mapping(src_mappings, in_lang='crj', out_lang='crj-ipa')
        mapping = create_mapping(src_mapping, self.target_mapping)
        transducer = Transducer(mapping)
        self.assertEqual(transducer('t͡ʃi'), 'tʃi')
        self.assertEqual(transducer('t͡ʃu'), 'tʃu')
        self.assertEqual(transducer('t͡ʃa'), 'tʃɑ')

    def test_long_mappings(self):
        src_mappings = [
                {"in": "ᐧᐯ", "out": "pʷeː"},
                {"in": "ᐧᑌ", "out": "tʷeː"},
                {"in": "ᐧᑫ", "out": "kʷeː"},
            ]
        src_mapping = Mapping(src_mappings, in_lang='crj', out_lang='crj-ipa')
        mapping = create_mapping(src_mapping, self.target_mapping)
        transducer = Transducer(mapping)
        self.assertEqual(transducer('pʷeː'), 'pweː')
        self.assertEqual(transducer('tʷeː'), 'tweː')
        self.assertEqual(transducer('kʷeː'), 'kweː')


if __name__ == '__main__':
    main()
