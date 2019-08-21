"""

Module for all things related to lookup tables

"""

import csv
import os
import unicodedata as ud
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
from g2p.mappings.utils import create_fixed_width_lookbehind, escape_special_characters
from g2p.mappings.utils import flatten_abbreviations, load_abbreviations_from_file
from g2p.mappings.utils import load_from_file, unicode_escape, validate
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
        self.possible_kwargs = ['as_is', 'authors', 'case_sensitive', 'escape_special', 'in_lang', 'norm_form', 'out_lang', 'reverse']
        self.kwargs = OrderedDict(kwargs)
        self.allowable_norm_forms = ['NFC', 'NKFC', 'NFD', 'NFKD']
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
            self.mapping, self.kwargs = self.load_mapping_from_path(mapping)
        else:
            if "in_lang" in kwargs and "out_lang" in kwargs:
                self.mapping, self.kwargs = self.find_mapping(
                    kwargs['in_lang'], kwargs['out_lang'])
            else:
                raise exceptions.MalformedLookup()
        if self.abbreviations:
            for abb, stands_for in self.abbreviations.items():
                abb_match = re.compile(abb)
                abb_repl = '|'.join(stands_for)
                for io in self.mapping:
                    for key in io.keys():
                        if re.search(abb_match, io[key]):
                            io[key] = re.sub(abb_match, abb_repl, io[key])
        if not self.processed:
            self.mapping = self.process_kwargs(self.mapping)

    def __len__(self):
        return len(self.mapping)

    def __call__(self):
        return self.mapping

    def __iter__(self):
        return iter(self.mapping)

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
                            io[k] = self.normalize(v)
                #TODO: Should all of these also apply to abbreviations?
                if self.abbreviations:
                    self.abbreviations = {self.normalize(abb): [self.normalize(
                        x) for x in stands_for] for abb, stands_for in self.abbreviations.items()}
            if kwarg == 'reverse' and val:
                mapping = self.reverse_mappings(mapping)
        # After all processing is done, turn into regex
        for io in mapping:
            io['match_pattern'] = self.rule_to_regex(io)
        self.processed = True
        return mapping

    def normalize(self, inp: str):
        ''' Normalize to NFC(omposed) or NFD(ecomposed).
            Also, find any Unicode Escapes & decode 'em!
        '''
        if self.kwargs['norm_form'] not in self.allowable_norm_forms:
            raise exceptions.InvalidNormalization(self.normalize)
        else:
            normalized = ud.normalize(self.kwargs['norm_form'], unicode_escape(inp))
            if normalized != inp:
                LOGGER.info(
                    'The string %s was normalized to %s using the %s standard and by decoding any Unicode escapes. Note that this is not necessarily the final stage of normalization.',
                    inp, normalized, self.kwargs['norm_form'])
            return normalized

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
            raise Exception(
                'Your regex is malformed.')
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
                return mapping['mapping_data'], OrderedDict({k: v for k, v in mapping.items() if k in self.possible_kwargs})
        return [], OrderedDict()
    
    def load_mapping_from_path(self, path: str) -> list:
        path = Path(path)
        if path.exists() and (path.suffix.endswith('yml') or path.suffix.endswith('yaml')):
            with open(path) as f:
                mapping = yaml.safe_load(f)
            mapping['mapping_data'] = load_from_file(os.path.join(path.parent, mapping['mapping']))
            return mapping['mapping_data'], OrderedDict({k: v for k, v in mapping.items() if k in self.possible_kwargs})
        else:
            raise exceptions.MalformedMapping


if __name__ == '__main__':
    pass