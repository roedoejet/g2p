""" Test Mapping utility functions
"""

import os
from unittest import main, TestCase

from g2p.mappings import utils
from g2p.tests.public import PUBLIC_DIR
from g2p.exceptions import IncorrectFileType, MalformedMapping


class UtilsTester(TestCase):
    def setUp(self):
        pass

    def test_abb_flatten(self):
        pass

    def test_abb_expand(self):
        pass

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
            PUBLIC_DIR, 'mappings', 'minimal_config.yaml'), 1)
        xlsx = utils.load_mapping_from_path(os.path.join(
            PUBLIC_DIR, 'mappings', 'minimal_configs.yaml'), 2)
        # breakpoint()
        self.assertEqual(minimal, csv)
        self.assertEqual(minimal, json)
        self.assertEqual(minimal, xlsx)

    def test_validate(self):
        pass

    def test_escape_special(self):
        pass

    def test_load_abbs(self):
        with self.assertRaises(IncorrectFileType):
            utils.load_abbreviations_from_file(os.path.join(
                PUBLIC_DIR, 'mappings', 'abbreviations.json'))
        abbs = utils.load_abbreviations_from_file(
            os.path.join(PUBLIC_DIR, 'mappings', 'abbreviations.csv'))
        self.assertTrue("VOWEL" in abbs)
        self.assertEqual(abbs['VOWEL'], ['a', 'e', 'i', 'o', 'u'])

if __name__ == '__main__':
    main()
