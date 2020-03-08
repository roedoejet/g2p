from unittest import main, TestCase
import os
import json
from g2p.mappings import Mapping
from g2p.transducer import Transducer
from g2p.tests.public import __file__ as public_data
import unicodedata as ud

class MappingTest(TestCase):
    ''' Basic Mapping Test
    '''

    def setUp(self):
        self.test_mapping_no_norm = Mapping([{'in': '\u00e1', 'out': '\u00e1'}, {'in': '\u0061\u0301', 'out': '\u0061\u0301'}], norm_form='none')
        self.test_mapping_norm = Mapping([{'in': '\u00e1', 'out': '\u00e1'}])
        with open(os.path.join(os.path.dirname(public_data), 'git_to_ipa.json'), encoding='utf8') as f:
            self.json_map = json.load(f)
    
    def test_normalization(self):
        self.assertEqual(ud.normalize('NFD', '\u00e1'), self.test_mapping_norm.mapping[0]['in'])
        self.assertNotEqual(self.test_mapping_norm.mapping[0]['in'], '\u00e1')
        self.assertEqual(self.test_mapping_norm.mapping[0]['in'], '\u0061\u0301')
        self.assertEqual(self.test_mapping_no_norm.mapping[0]['in'], '\u00e1')
        self.assertEqual(self.test_mapping_no_norm.mapping[0]['out'], '\u00e1')
        self.assertEqual(self.test_mapping_no_norm.mapping[1]['in'], '\u0061\u0301')
        self.assertEqual(self.test_mapping_no_norm.mapping[1]['out'], '\u0061\u0301')

    def test_json_map(self):
        json_map = Mapping(self.json_map['map'], **{k:v for k,v in self.json_map.items() if k != 'map'})
        self.assertEqual(len(json_map), 34)
        self.assertTrue(json_map.kwargs['in_metadata']['case_insensitive'])

    def test_as_is(self):
        mapping = Mapping([{'in': 'a', "out": 'b'}, {'in': 'aa', 'out': 'c'}], as_is=False)
        mapping_as_is = Mapping([{'in': 'a', "out": 'b'}, {'in': 'aa', 'out': 'c'}])
        transducer = Transducer(mapping)
        transducer_as_is = Transducer(mapping_as_is)
        self.assertEqual(transducer('aa').output_string, 'c')
        self.assertEqual(transducer_as_is('aa').output_string, 'bb')

    def test_case_sensitive(self):
        mapping = Mapping([{'in': 'A', "out": 'b'}], case_sensitive=False)
        mapping_case_sensitive = Mapping([{'in': 'A', "out": 'b'}])
        transducer = Transducer(mapping)
        transducer_case_sensitive = Transducer(mapping_case_sensitive)
        self.assertEqual(transducer('a').output_string, 'b')
        self.assertEqual(transducer_case_sensitive('a').output_string, 'a')
        self.assertEqual(transducer('A').output_string, 'b')

    def test_escape_special(self):
        mapping = Mapping([{'in': '\d', "out": 'digit'}])
        mapping_escaped = Mapping([{'in': '\d', "out": 'b'}], escape_special=True)
        transducer = Transducer(mapping)
        transducer_escaped = Transducer(mapping_escaped)
        self.assertEqual(transducer('1').output_string, 'digit')
        self.assertEqual(transducer('\d').output_string, '\d')
        self.assertEqual(transducer_escaped('1').output_string, '1')
        self.assertEqual(transducer_escaped('\d').output_string, 'b')

    def test_norm_form(self):
        mapping_nfc = Mapping([{'in': 'a\u0301', "out": 'a'}]) # Defaults to NFC
        mapping_nfd = Mapping([{'in': 'a\u0301', "out": 'a'}], norm_form='NFD')
        mapping_none = Mapping([{'in': 'a\u0301', "out": 'a'}], norm_form=False)

        transducer_nfc = Transducer(mapping_nfc)
        transducer_nfd = Transducer(mapping_nfd)
        transducer_none = Transducer(mapping_none)

        self.assertEqual(transducer_nfc('a\u0301').output_string, 'a')
        self.assertEqual(transducer_nfc('\u00E1').output_string, 'a')
        self.assertEqual(transducer_nfd('a\u0301').output_string, 'a')
        self.assertEqual(transducer_nfd('\u00E1').output_string, 'a')
        self.assertEqual(transducer_none('a\u0301').output_string, 'a')
        self.assertEqual(transducer_none('\u00E1').output_string, '\u00E1')

    def test_reverse(self):
        mapping = Mapping([{'in': 'a', "out": 'b'}])
        mapping_reversed = Mapping([{'in': 'a', "out": 'b'}], reverse=True)
        transducer = Transducer(mapping)
        transducer_reversed = Transducer(mapping_reversed)
        self.assertEqual(transducer('a').output_string, 'b')
        self.assertEqual(transducer('b').output_string, 'b')
        self.assertEqual(transducer_reversed('a').output_string, 'a')
        self.assertEqual(transducer_reversed('b').output_string, 'a')

    def test_minimal(self):
        mapping = Mapping(os.path.join(os.path.dirname(public_data), 'mappings', 'minimal_config.yaml'))
        transducer = Transducer(mapping)
        self.assertEqual(transducer('abb').output_string, 'aab')
        self.assertEqual(transducer('a').output_string, 'a')
        self.assertTrue(mapping.kwargs['as_is'])
        self.assertFalse(mapping.kwargs['case_sensitive'])
        self.assertTrue(mapping.kwargs['escape_special'])
        self.assertEqual(mapping.kwargs['norm_form'], 'NFD')
        self.assertTrue(mapping.kwargs['reverse'])

    def test_null_input(self):
        mapping = Mapping([{'in': '', 'out': 'a'}])
        self.assertFalse(mapping())

    def test_no_escape(self):
        mapping = Mapping(os.path.join(os.path.dirname(public_data), 'mappings', 'no_escape.csv'))
        transducer = Transducer(mapping)
        self.assertEqual(transducer('?').output_string, 'ʔ')

if __name__ == "__main__":
    main()