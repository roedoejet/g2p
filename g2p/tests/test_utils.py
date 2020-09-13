#!/usr/bin/env python3

""" Test Mapping utility functions
"""

import os
from unittest import main, TestCase
from collections import defaultdict

import yaml

from g2p.mappings import utils
from g2p.mappings import Mapping
from g2p.tests.public import PUBLIC_DIR
from g2p.exceptions import IncorrectFileType, MalformedMapping


class UtilsTest(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        gen_mapping = os.path.join(PUBLIC_DIR, 'mappings', 'test_to_test-out.json')
        gen_config = os.path.join(PUBLIC_DIR, 'mappings', 'test_config.yaml')
        if os.path.exists(gen_config):
            os.remove(gen_config)
        if os.path.exists(gen_mapping):
            os.remove(gen_mapping)
        fresh_config = {'language_name': 'generated', 'mappings': []}
        with open(os.path.join(PUBLIC_DIR, 'mappings', 'generated_add.yaml'), 'w') as f:
            yaml.dump(fresh_config, f, Dumper=utils.IndentDumper, default_flow_style=False)

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
        tsv = utils.load_mapping_from_path(os.path.join(
            PUBLIC_DIR, 'mappings', 'minimal_configs.yaml'), 1)
        psv = utils.load_mapping_from_path(os.path.join(
            PUBLIC_DIR, 'mappings', 'minimal_configs.yaml'), 2)
        json = utils.load_mapping_from_path(os.path.join(
            PUBLIC_DIR, 'mappings', 'minimal_configs.yaml'), 3)
        xlsx = utils.load_mapping_from_path(os.path.join(
            PUBLIC_DIR, 'mappings', 'minimal_configs.yaml'), 4)
        self.assertEqual(minimal['mapping_data'], csv['mapping_data'])
        self.assertEqual(minimal['mapping_data'], tsv['mapping_data'])
        self.assertEqual(minimal['mapping_data'], psv['mapping_data'])
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
        for abb in ['abbreviations.csv', 'abbreviations.tsv', 'abbreviations.psv']:
            abbs = utils.load_abbreviations_from_file(
                os.path.join(PUBLIC_DIR, 'mappings', abb))
            self.assertTrue("VOWEL" in abbs)
            self.assertEqual(abbs['VOWEL'], ['a', 'e', 'i', 'o', 'u'])

    def test_generated_mapping(self):
        config = {'in_lang': 'test', 'out_lang': 'test-out', 'rule_ordering': "apply-longest-first"}
        # config = utils.generate_config('test', 'test-out', 'Test', 'TestOut')
        config['mapping'] = [{'in': 'a', 'out': 'b'}]
        mapping = Mapping(**config)
        mapping.config_to_file(os.path.join(PUBLIC_DIR, 'mappings', 'test_config.yaml'))
        mapping.config_to_file(os.path.join(PUBLIC_DIR, 'mappings', 'generated_add.yaml'))
        mapping.mapping_to_file(os.path.join(PUBLIC_DIR, 'mappings'))
        test_config = utils.load_mapping_from_path(os.path.join(
            PUBLIC_DIR, 'mappings', 'test_config.yaml'))
        test_config_added = utils.load_mapping_from_path(os.path.join(
            PUBLIC_DIR, 'mappings', 'generated_add.yaml'))
        self.assertEqual(test_config['mapping_data'], [{'in': 'a', 'out': 'b', 'context_before': '', 'context_after': ''}])
        self.assertEqual(test_config['in_lang'], 'test')
        self.assertEqual(test_config['out_lang'], 'test-out')
        self.assertEqual(test_config['language_name'], 'test')
        self.assertEqual(test_config['display_name'], 'test custom to test-out custom')
        self.assertEqual(test_config_added['mapping_data'], [{'in': 'a', 'out': 'b', 'context_before': '', 'context_after': ''}])
        self.assertEqual(test_config_added['in_lang'], 'test')
        self.assertEqual(test_config_added['out_lang'], 'test-out')
        self.assertEqual(test_config_added['language_name'], 'test')
        self.assertEqual(test_config_added['display_name'], 'test custom to test-out custom')

if __name__ == '__main__':
    main()
