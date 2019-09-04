""" Test Mapping utility functions
"""

import os
from unittest import main, TestCase
from collections import defaultdict

from g2p.mappings import utils
from g2p.tests.public import PUBLIC_DIR
from g2p.exceptions import IncorrectFileType, MalformedMapping
from g2p.transducer.utils import convert_index_to_tuples, convert_tuples_to_index


class UtilsTest(TestCase):
    def setUp(self):
        pass

    def test_abb_flatten_and_expand(self):
        test_rows = [
            ["VOWEL", 'a', 'e', 'i', 'o', 'u'],
            ["OTHER", 't', 'e', 's', 't']
        ]
        default_dict = defaultdict(list)
        default_dict['VOWEL'].extend(['a', 'e', 'i', 'o', 'u'])
        default_dict['OTHER'].extend(['t', 'e', 's', 't'])
        empty_rows = []
        while len(empty_rows) < 10:
            empty_rows.append(['', '', '', '', '', ''])
        self.assertEqual(utils.flatten_abbreviations(test_rows), default_dict)
        self.assertEqual(utils.expand_abbreviations(default_dict), test_rows)
        self.assertEqual(utils.expand_abbreviations({}), empty_rows)

    def test_unicode_escape(self):
        ''' Should turn \u0331 declared in CSVs
            into actual Unicode string for that codepoint
        '''
        self.assertEqual('\u0000', utils.unicode_escape('\\u0000'))
        self.assertEqual('\u0331', utils.unicode_escape('\\u0331'))
        self.assertEqual('\u26F0', utils.unicode_escape('\\u26F0'))

    def test_fixed_width(self):
        # TODO: Test utils.create_fixed_width_lookbehind and utils.pattern_to_fixed_width_lookbehinds
        pass

    def test_pattern(self):
        pass

    def test_load_mapping(self):
        with self.assertRaises(MalformedMapping):
            utils.load_mapping_from_path(os.path.join(
                PUBLIC_DIR, 'mappings', 'malformed_config.yaml'))
        minimal = utils.load_mapping_from_path(os.path.join(
            PUBLIC_DIR, 'mappings', 'minimal_config.yaml'))
        csv = utils.load_mapping_from_path(os.path.join(
            PUBLIC_DIR, 'mappings', 'minimal_configs.yaml'), 0)
        json = utils.load_mapping_from_path(os.path.join(
            PUBLIC_DIR, 'mappings', 'minimal_configs.yaml'), 1)
        xlsx = utils.load_mapping_from_path(os.path.join(
            PUBLIC_DIR, 'mappings', 'minimal_configs.yaml'), 2)
        self.assertEqual(minimal['mapping_data'], csv['mapping_data'])
        self.assertEqual(minimal['mapping_data'], json['mapping_data'])
        self.assertEqual(minimal['mapping_data'], xlsx['mapping_data'])

    def test_validate(self):
        pass

    def test_escape_special(self):
        self.assertEqual(utils.escape_special_characters({'in': '?'}), {'in': '\?'})

    def test_load_abbs(self):
        with self.assertRaises(IncorrectFileType):
            utils.load_abbreviations_from_file(os.path.join(
                PUBLIC_DIR, 'mappings', 'abbreviations.json'))
        abbs = utils.load_abbreviations_from_file(
            os.path.join(PUBLIC_DIR, 'mappings', 'abbreviations.csv'))
        self.assertTrue("VOWEL" in abbs)
        self.assertEqual(abbs['VOWEL'], ['a', 'e', 'i', 'o', 'u'])

    def test_tuple_dict_conversion(self):
        tuple_format = [
            ((0, 'a'), (0, 'b'))
        ]
        dict_format = {0: {'input_string': 'a', 'output': {0: 'b'}}}
        self.assertEqual(convert_index_to_tuples(dict_format), tuple_format)
        self.assertEqual(convert_tuples_to_index(tuple_format), dict_format)


if __name__ == '__main__':
    main()
