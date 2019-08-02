from unittest import main, TestCase
import os
import json
from g2p.mappings import Mapping
from g2p.tests.public import __file__ as public_data
import unicodedata as ud

class MappingTest(TestCase):
    ''' Basic Mapping Test
    '''

    def setUp(self):
        self.test_mapping_norm = Mapping([{'in': '\u0061\u0301', 'out': '\u0061\u0301'}])
        with open(os.path.join(os.path.dirname(public_data), 'git_to_ipa.json')) as f:
            self.json_map = json.load(f)
    
    def test_normalization(self):
        self.assertEqual(ud.normalize('NFC', '\u0061\u0301'), self.test_mapping_norm.mapping[0]['in'])
        self.assertEqual(self.test_mapping_norm.mapping[0]['in'], '\u00e1')
        self.assertNotEqual(self.test_mapping_norm.mapping[0]['in'], '\u0061\u0301')

    def test_json_map(self):
        json_map = Mapping(self.json_map['map'], **{k:v for k,v in self.json_map.items() if k != 'map'})
        self.assertEqual(len(json_map), 34)
        self.assertTrue(json_map.kwargs['in_metadata']['case_insensitive'])

if __name__ == "__main__":
    main()