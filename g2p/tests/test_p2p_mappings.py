"""
Test all Mappings
"""

from unittest import TestCase

import g2p.create_ipa_mapping as mapper

def make_map_dict(mapping):
    return dict((m['in'], m['out']) for m in mapping['map'])

class TestMappings(TestCase):
    def setUp(self):
        self.target_mapping = {
            "type": "mapping",
            "in_metadata": {
                "lang": "eng-ipa",
                "format": "ipa",
                "delimiter": ""
            },
            "out_metadata": {
                "lang": "eng-arpabet",
                "format": "arpabet",
                "delimiter": " "
            },
            "map": [
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
        }

    def test_unigram_mappings(self):
        src_mapping = {
            "type": "mapping",
            "in_metadata": {
                "lang": "crj",
                "format": "custom",
                "delimiter": ""
            },
            "out_metadata": {
                "lang": "crj-ipa",
                "format": "ipa",
                "delimiter": ""
            },
            "map": [
                {"in": "ᐃ", "out": "i"},
                {"in": "ᐅ", "out": "u"},
                {"in": "ᐊ", "out": "a"},
            ],
        }
        mapping = make_map_dict(mapper.create_mapping(src_mapping,
                                                      self.target_mapping))
        self.assertEqual(mapping['a'], 'ɑ')
        self.assertEqual(mapping['i'], 'i')
        self.assertEqual(mapping['u'], 'u')

    def test_bigram_mappings(self):
        src_mapping = {
            "type": "mapping",
            "in_metadata": {
                "lang": "crj",
                "format": "custom",
                "delimiter": ""
            },
            "out_metadata": {
                "lang": "crj-ipa",
                "format": "ipa",
                "delimiter": ""
            },
            "map": [
                {"in": "ᐱ", "out": "pi"},
                {"in": "ᑎ", "out": "ti"},
                {"in": "ᑭ", "out": "ki"},
            ],
        }
        mapping = make_map_dict(mapper.create_mapping(src_mapping,
                                                      self.target_mapping))
        self.assertEqual(mapping['pi'], 'pi')
        self.assertEqual(mapping['ti'], 'ti')
        self.assertEqual(mapping['ki'], 'ki')

    def test_trigram_mappings(self):
        src_mapping = {
            "type": "mapping",
            "in_metadata": {
                "lang": "crj",
                "format": "custom",
                "delimiter": ""
            },
            "out_metadata": {
                "lang": "crj-ipa",
                "format": "ipa",
                "delimiter": ""
            },
            "map": [
                {"in": "ᒋ", "out": "t͡ʃi"},
                {"in": "ᒍ", "out": "t͡ʃu"},
                {"in": "ᒐ", "out": "t͡ʃa"},
            ],
        }
        mapping = make_map_dict(mapper.create_mapping(src_mapping,
                                                      self.target_mapping))
        self.assertEqual(mapping['t͡ʃi'], 'tʃi')
        self.assertEqual(mapping['t͡ʃu'], 'tʃu')
        self.assertEqual(mapping['t͡ʃa'], 'tʃɑ')

    def test_long_mappings(self):
        src_mapping = {
            "type": "mapping",
            "in_metadata": {
                "lang": "crj",
                "format": "custom",
                "delimiter": ""
            },
            "out_metadata": {
                "lang": "crj-ipa",
                "format": "ipa",
                "delimiter": ""
            },
            "map": [
                {"in": "ᐧᐯ", "out": "pʷeː"},
                {"in": "ᐧᑌ", "out": "tʷeː"},
                {"in": "ᐧᑫ", "out": "kʷeː"},
            ],
        }
        mapping = make_map_dict(mapper.create_mapping(src_mapping,
                                                      self.target_mapping))
        self.assertEqual(mapping['pʷeː'], 'pweː')
        self.assertEqual(mapping['tʷeː'], 'tweː')
        self.assertEqual(mapping['kʷeː'], 'kweː')
