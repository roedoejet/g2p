"""

Module for all things related to lookup tables

"""

import csv
import os
import re
import json
from typing import DefaultDict, List, Pattern, Union
from collections import defaultdict, OrderedDict
from itertools import chain
from pathlib import Path
from operator import methodcaller

import yaml

from g2p import exceptions
from g2p.mappings.langs import __file__ as LANGS_FILE, LANGS, MAPPINGS_AVAILABLE
from g2p.mappings.utils import create_fixed_width_lookbehind, escape_special_characters, normalize
from g2p.mappings.utils import flatten_abbreviations, IndentDumper, load_abbreviations_from_file
from g2p.mappings.utils import load_from_file, load_mapping_from_path, unicode_escape, validate
from g2p.log import LOGGER


class Mapping():
    """ Class for lookup tables

        @param as_is: bool = False
            Evaluate g2p rules in mapping in the order they are.
            Default is to reverse sort them by length.

        @param case_sensitive: bool = True
            Lower all rules and conversion input

        @param escape_special: bool = False
            Escape special characters in rules

        @param norm_form: str = "NFC"
            Normalization standard to follow. NFC | NKFC | NFD | NKFD

        @param reverse: bool = False
            Reverse all mappings

    """

    def __init__(self, mapping=None, abbreviations: Union[str, DefaultDict[str, List[str]]] = False, **kwargs):
        # should these just be explicit instead of kwargs...
        self.allowable_kwargs = ['language_name', 'display_name', 'mapping', 'in_lang',
                                 'out_lang', 'out_delimiter', 'as_is', 'case_sensitive', 'escape_special', 'norm_form', 'reverse']
        self.kwargs = OrderedDict(kwargs)
        self.processed = False
        if isinstance(abbreviations, defaultdict) or not abbreviations:
            self.abbreviations = abbreviations
        elif abbreviations:
            self.abbreviations = load_abbreviations_from_file(
                abbreviations)
        # Handle user-supplied list
        if isinstance(mapping, list):
            self.mapping = validate(mapping)
        elif isinstance(mapping, str):
            loaded_config = load_mapping_from_path(mapping)
            self.process_loaded_config(loaded_config)
        else:
            if "in_lang" in self.kwargs and "out_lang" in self.kwargs:
                loaded_config = self.find_mapping(
                    self.kwargs['in_lang'], self.kwargs['out_lang'])
                self.process_loaded_config(loaded_config)
            elif 'id' in self.kwargs:
                loaded_config = self.find_mapping_by_id(self.kwargs['id'])
                self.process_loaded_config(loaded_config)
            else:
                raise exceptions.MalformedLookup()
        if self.abbreviations:
            for abb, stands_for in self.abbreviations.items():
                abb_match = re.compile(abb)
                abb_repl = '|'.join(stands_for)
                if self.mapping and 'match_pattern' not in self.mapping[0]:
                    for io in self.mapping:
                        for key in io.keys():
                            if key in ['in', 'out', 'context_before', 'context_after'] and re.search(abb_match, io[key]):
                                io[key] = re.sub(
                                    abb_match, unicode_escape(abb_repl), io[key])
        if not self.processed:
            self.mapping = self.process_kwargs(self.mapping)

    def __len__(self):
        return len(self.mapping)

    def __call__(self):
        return self.mapping

    def __iter__(self):
        return iter(self.mapping)

    def inventory(self, in_or_out: str = 'in'):
        ''' Return just inputs or outputs as inventory of mapping
        '''
        return [x[in_or_out] for x in self.mapping]

    def process_loaded_config(self, config):
        ''' For a mapping loaded from a file, take the keyword arguments and supply them to the
            Mapping, and get any abbreviations data.
        '''
        self.mapping = config['mapping_data']
        mapping_kwargs = OrderedDict(
            {k: v for k, v in config.items() if k in self.allowable_kwargs})
        self.abbreviations = config.get('abbreviations_data', None)
        # Merge kwargs, but prioritize kwargs that initialized the Mapping
        self.kwargs = {**mapping_kwargs, **self.kwargs}

    def plain_mapping(self):
        ''' Return mapping
        '''
        return [{k: v for k, v in io.items() if k in ['in', 'out', 'context_before', 'context_after']} for io in self.mapping]

    def process_kwargs(self, mapping):
        ''' Apply kwargs in the order they are provided. kwargs are ordered as of python 3.6
        '''
        # Add defaults
        if 'as_is' not in self.kwargs:
            self.kwargs['as_is'] = False
        if 'case_sensitive' not in self.kwargs:
            self.kwargs['case_sensitive'] = True
        if 'escape_special' not in self.kwargs:
            self.kwargs['escape_special'] = False
        if 'norm_form' not in self.kwargs:
            self.kwargs['norm_form'] = 'NFC'
        if 'reverse' not in self.kwargs:
            self.kwargs['reverse'] = False
        # Process kwargs in order received
        for kwarg, val in self.kwargs.items():
            if kwarg == 'as_is' and not val:
                # sort by reverse len
                mapping = sorted(mapping, key=lambda x: len(
                    x["in"]), reverse=True)
            if kwarg == 'escape_special' and val:
                mapping = [escape_special_characters(x) for x in mapping]
            if kwarg == 'case_sensitive' and not val:
                mapping = self.lower_mappings(mapping)
            if kwarg == 'norm_form' and val:
                for io in mapping:
                    for k, v in io.items():
                        if isinstance(v, str):
                            io[k] = normalize(v, self.kwargs['norm_form'])
            if kwarg == 'reverse' and val:
                mapping = self.reverse_mappings(mapping)
        # After all processing is done, turn into regex
        for io in mapping:
            io['match_pattern'] = self.rule_to_regex(io)
        self.processed = True
        return mapping

    def rule_to_regex(self, rule: str) -> Pattern:
        """Turns an input string (and the context) from an input/output pair
        into a regular expression pattern"""
        if "context_before" in rule and rule['context_before']:
            before = rule["context_before"]
        else:
            before = ''
        if 'context_after' in rule and rule['context_after']:
            after = rule["context_after"]
        else:
            after = ''
        input_match = re.sub(re.compile(
            r'{\d+}'), "", rule['in'])
        try:
            inp = create_fixed_width_lookbehind(before) + input_match
            if after:
                inp += f"(?={after})"
            if not self.kwargs['case_sensitive']:
                rule_regex = re.compile(inp, re.I)
            else:
                rule_regex = re.compile(inp)
        except:
            LOGGER.error(f'Your regex in mapping between {self.kwargs["in_lang"]} and {self.kwargs["out_lang"]} is malformed. \
                    Do you have un-escaped regex characters in your input {inp}, contexts {before}, {after}?')
            raise Exception(
                f'Your regex in mapping between {self.kwargs["in_lang"]} and {self.kwargs["out_lang"]} is malformed. \
                    Do you have un-escaped regex characters in your input {inp}, contexts {before}, {after}?')
        return rule_regex

    def reverse_mappings(self, mapping):
        ''' Reverse the mapping
        '''
        for io in mapping:
            io['in'], io['out'] = io['out'], io['in']
        return mapping

    def lower_mappings(self, mapping):
        ''' Lower the mapping
        '''
        for io in mapping:
            for k, v in io.items():
                if k in ['in', 'out', 'context_before', 'context_after']:
                    io[k] = v.lower()
        return mapping

    def add_abbreviations(self, abbs, mappings):
        ''' Return abbreviated forms, given a list of abbreviations.

        {'in': 'a', 'out': 'b', 'context_before': 'V', 'context_after': '' }
        {'abbreviation': 'V', 'stands_for': ['a','b','c']}
        ->
        {'in': 'a', 'out': 'b', 'context_before': 'a|b|c', 'context_after': ''}
        '''
        for abb in abbs:
            for io in mappings:
                for key in io.keys():
                    if io[key] == abb['abbreviation']:
                        io[key] = abb['stands_for']
        return mappings

    def find_mapping(self, in_lang: str, out_lang: str) -> list:
        ''' Given an input and output, find a mapping to get between them.
        '''
        for mapping in MAPPINGS_AVAILABLE:
            map_in_lang = mapping.get('in_lang', '')
            map_out_lang = mapping.get('out_lang', '')
            if map_in_lang == in_lang and map_out_lang == out_lang:
                return mapping
        raise exceptions.MappingMissing(in_lang, out_lang)

    def find_mapping_by_id(self, map_id: str):
        ''' Find the mapping with a given ID
        '''
        for mapping in MAPPINGS_AVAILABLE:
            if mapping.get('id', '') == map_id:
                return mapping

    def mapping_to_file(self, output_path: str, file_type: str):
        ''' Write mapping to file
        '''
        if not os.path.isdir(output_path):
            raise Exception("Path %s is not a directory", output_path)
        fn = os.path.join(output_path, self.kwargs.get('in_lang', 'und') + "_to_" +
                          self.kwargs.get('out_lang', 'und') + "." + file_type)
        fieldnames = ['in', 'out', 'context_before', 'context_after']
        filtered = [{k: v for k, v in io.items() if k in fieldnames}
                    for io in self.mapping]
        if file_type == 'json':
            with open(fn, 'w') as f:
                json.dump(filtered, f, indent=4)
        elif file_type == 'csv':
            with open(fn, 'w') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                for io in filtered:
                    writer.writerow(io)
        else:
            raise exceptions.IncorrectFileType

    def config_to_file(self, output_path: str, mapping_type: str):
        ''' Write config to file
        '''
        if not os.path.isdir(output_path):
            raise Exception("Path %s is not a directory", output_path)
        fn = os.path.join(output_path, 'config.yaml')
        template = {"mappings": [
            {
                "language_name": self.kwargs.get('language_name', self.kwargs.get('in_lang', 'und')),
                "display_name": self.kwargs.get('display_name', self.kwargs.get('in_lang', 'und') + " to " + self.kwargs.get('out_lang', 'und')),
                "in_lang": self.kwargs.get('in_lang', 'und'),
                "out_lang": self.kwargs.get('out_lang', 'und'),
                "authors": self.kwargs.get('authors', ['generated']),
                "as_is": self.kwargs.get('as_is', False),
                "case_sensitive": self.kwargs.get('case_sensitive', True),
                "escape_special": self.kwargs.get('escape_special', False),
                "norm_form": self.kwargs.get('norm_form', "NFC"),
                "reverse": self.kwargs.get('reverse', False),
                "mapping": self.kwargs.get('in_lang', 'und') + "_to_" +
                self.kwargs.get('out_lang', 'und') + "." + mapping_type
            }
        ]}
        with open(fn, 'w') as f:
            yaml.dump(template, f, Dumper=IndentDumper,
                      default_flow_style=False)

    def to_file(self, output_path: str, mapping_type: str = 'csv'):
        self.mapping_to_file(output_path, mapping_type)
        self.config_to_file(output_path, mapping_type)


if __name__ == '__main__':
    pass
