#!/usr/bin/env python3

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
        self.assertEqual(transducer('a').output_string, 'ɑ')
        self.assertEqual(transducer('i').output_string, 'i')
        self.assertEqual(transducer('u').output_string, 'u')

    def test_bigram_mappings(self):
        src_mappings = [
            {"in": "ᐱ", "out": "pi"},
            {"in": "ᑎ", "out": "ti"},
            {"in": "ᑭ", "out": "ki"},
        ]
        src_mapping = Mapping(src_mappings, in_lang='crj', out_lang='crj-ipa')
        mapping = create_mapping(src_mapping, self.target_mapping)
        transducer = Transducer(mapping)
        self.assertEqual(transducer('pi').output_string, 'pi')
        self.assertEqual(transducer('ti').output_string, 'ti')
        self.assertEqual(transducer('ki').output_string, 'ki')

    def test_trigram_mappings(self):
        src_mappings = [
            {"in": "ᒋ", "out": "t͡ʃi"},
            {"in": "ᒍ", "out": "t͡ʃu"},
            {"in": "ᒐ", "out": "t͡ʃa"},
        ]
        src_mapping = Mapping(src_mappings, in_lang='crj', out_lang='crj-ipa')
        mapping = create_mapping(src_mapping, self.target_mapping)
        transducer = Transducer(mapping)
        self.assertEqual(transducer('t͡ʃi').output_string, 'tʃi')
        self.assertEqual(transducer('t͡ʃu').output_string, 'tʃu')
        self.assertEqual(transducer('t͡ʃa').output_string, 'tʃɑ')

    def test_long_mappings(self):
        src_mappings = [
                {"in": "ᐧᐯ", "out": "pʷeː"},
                {"in": "ᐧᑌ", "out": "tʷeː"},
                {"in": "ᐧᑫ", "out": "kʷeː"},
            ]
        src_mapping = Mapping(src_mappings, in_lang='crj', out_lang='crj-ipa')
        mapping = create_mapping(src_mapping, self.target_mapping)
        transducer = Transducer(mapping)
        self.assertEqual(transducer('pʷeː').output_string, 'pweː')
        self.assertEqual(transducer('tʷeː').output_string, 'tweː')
        self.assertEqual(transducer('kʷeː').output_string, 'kweː')


if __name__ == '__main__':
    main()
