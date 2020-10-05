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
from copy import deepcopy

import yaml
import datetime as dt

from g2p import exceptions
from g2p.mappings.langs import __file__ as LANGS_FILE, LANGS, MAPPINGS_AVAILABLE
from g2p.mappings.utils import create_fixed_width_lookbehind, escape_special_characters, normalize
from g2p.mappings.utils import find_mapping, flatten_abbreviations, IndentDumper, load_abbreviations_from_file
from g2p.mappings.utils import load_from_file, load_mapping_from_path, unicode_escape, validate
from g2p.mappings.utils import is_dummy, is_ipa, is_xsampa
from g2p.log import LOGGER

GEN_DIR = os.path.join(os.path.dirname(LANGS_FILE), 'generated')

class Mapping():
    """ Class for lookup tables

        @param as_is: bool = True
            Affects whether or not rules are sorted or left as is.
            Please use ``rule_ordering`` instead.
            If True, Evaluate g2p rules in mapping in the order they are written.
            If False, rules will be reverse sorted by length.

            .. deprecated:: 0.6
                use ``rule_ordering`` instead

        @param case_sensitive: bool = True
            Lower all rules and conversion input

        @param escape_special: bool = False
            Escape special characters in rules

        @param norm_form: str = "NFD"
            Normalization standard to follow. NFC | NKFC | NFD | NKFD | none

        @param out_delimiter: str = ""
            Separate output transformations with a delimiter

        @param reverse: bool = False
            Reverse all mappings

        @param rule_ordering: str = "as-written"
            Affects in what order the rules are applied.

            If set to ``"as-written"``, rules are applied from top-to-bottom in the order that they
            are written in the source file
            (previously this was accomplished with ``as_is=True``).

            If set to ``"apply-longest-first"``, rules are first sorted such that rules with the longest
            input are applied first. Sorting the rules like this prevents shorter rules
            from taking part in feeding relations
            (previously this was accomplished with ``as_is=False``).

        @param prevent_feeding: bool = False
            Converts each rule into an intermediary form

    """

    def __init__(self, mapping=None, abbreviations: Union[str, DefaultDict[str, List[str]]] = False, **kwargs):
        # should these just be explicit instead of kwargs...
        # yes, they should
        self.allowable_kwargs = ['language_name', 'display_name', 'mapping', 'in_lang',
                                 'out_lang', 'out_delimiter', 'as_is', 'case_sensitive', 'rule_ordering',
                                 'escape_special', 'norm_form', 'prevent_feeding', 'reverse']
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
        elif isinstance(mapping, str) and (mapping.endswith('yaml') or mapping.endswith('yml')):
            loaded_config = load_mapping_from_path(mapping)
            self.process_loaded_config(loaded_config)
        elif isinstance(mapping, str):
            self.mapping = validate(load_from_file(mapping))
        else:
            if "in_lang" in self.kwargs and "out_lang" in self.kwargs:
                loaded_config = find_mapping(
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

    def __getitem__(self, item):
        if isinstance(item, int):  # item is an integer
            return self.mapping[item]
        if isinstance(item, slice):  # item is a slice
            return self.mapping[item.start or 0:item.stop or len(self.mapping)]
        else:  # invalid index type
            raise TypeError('{cls} indices must be integers or slices, not {idx}'.format(
                cls=type(self).__name__,
                idx=type(item).__name__,
            ))

    @staticmethod
    def find_mapping_by_id(map_id: str):
        ''' Find the mapping with a given ID
        '''
        for mapping in MAPPINGS_AVAILABLE:
            if mapping.get('id', '') == map_id:
                return deepcopy(mapping)
    @staticmethod
    def mapping_type(name):
        if is_ipa(name):
            return 'IPA'
        elif is_xsampa(name):
            return 'XSAMPA'
        elif is_dummy(name):
            return 'dummy'
        else:
            return 'custom'

    @staticmethod
    def _string_to_pua(string: str, offset: int) -> str:
        """Given an string of length n, and an offset m,
           produce a string of n * chr(983040 + m).
           This makes use of the Supplementary Private Use Area A Unicode block.

        Args:
            string (str): The string to convert
            offset (int): The offset from the start of the Supplementary Private Use Area

        Returns:
            str: The resulting string
        """
        intermediate_char = chr(983040 + offset)
        return intermediate_char * len(string)

    def index(self, item):
        return self.mapping.index(item)

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
        return [{k: v for k, v in io.items() if k not in ['match_pattern', 'intermediate_form']} for io in self.mapping]

    def process_kwargs(self, mapping):
        ''' Apply kwargs in the order they are provided. kwargs are ordered as of python 3.6
        '''

        if 'as_is' in self.kwargs:
            as_is = self.kwargs['as_is']
            if as_is:
                appropriate_setting = "as-written"
            else:
                appropriate_setting = "apply-longest-first"

            self.kwargs["rule_ordering"] = appropriate_setting
            del self.kwargs["as_is"]

            LOGGER.warning(
                f"mapping from {self.kwargs.get('in_lang')} to {self.kwargs.get('out_lang')} "
                'is using the deprecated parameter "as_is"; '
                f"replace `as_is: {as_is}` with `rule_ordering: {appropriate_setting}`"
            )

        # Add defaults
        if 'rule_ordering' in self.kwargs:
            # right now, "rule-ordering" is a more explict alias of the "as-is" option.
            ordering = self.kwargs["rule_ordering"]
            if ordering not in ("as-written", "apply-longest-first"):
                LOGGER.error(
                    f"mapping from {self.kwargs.get('in_lang')} to {self.kwargs.get('out_lang')} "
                    f"has invalid value '{ordering}' for rule_ordering parameter; "
                    "rule_ordering must be one of "
                    '"as-written" or "apply-longest-first"'
                )
        else:
            self.kwargs["rule_ordering"] = "as-written"
        if 'case_sensitive' not in self.kwargs:
            self.kwargs['case_sensitive'] = True
        if 'escape_special' not in self.kwargs:
            self.kwargs['escape_special'] = False
        if 'norm_form' not in self.kwargs:
            self.kwargs['norm_form'] = 'NFD'
        if 'reverse' not in self.kwargs:
            self.kwargs['reverse'] = False
        if 'prevent_feeding' not in self.kwargs:
            self.kwargs['prevent_feeding'] = False
        if 'in_lang' not in self.kwargs:
            self.kwargs['in_lang'] = 'und'
        if 'out_lang' not in self.kwargs:
            self.kwargs['out_lang'] = 'und'

        # Process kwargs in order received
        for kwarg, val in self.kwargs.items():
            if kwarg == 'rule_ordering' and self.wants_rules_sorted():
                # sort by reverse len
                mapping = sorted(mapping, key=lambda x: len(
                    x["in"]), reverse=True)
            elif kwarg == 'escape_special' and val:
                mapping = [escape_special_characters(x) for x in mapping]
            elif kwarg == 'norm_form' and val:
                for io in mapping:
                    for k, v in io.items():
                        if isinstance(v, str):
                            io[k] = normalize(v, self.kwargs['norm_form'])
            elif kwarg == 'reverse' and val:
                mapping = self.reverse_mappings(mapping)
        # After all processing is done, turn into regex
        for io in mapping:
            if self.kwargs['prevent_feeding'] or ('prevent_feeding' in io and io['prevent_feeding']):
                io['intermediate_form'] = self._string_to_pua(
                    io['out'], mapping.index(io))
            io['match_pattern'] = self.rule_to_regex(io)
            if not io['match_pattern']:
                mapping.remove(io)
        self.processed = True
        return mapping

    def wants_rules_sorted(self) -> bool:
        """Returns whether the rules will be sorted prior to finalizing the mapping.

        Returns:
            bool: True if the rules should be sorted.
        """
        return self.kwargs['rule_ordering'] == 'apply-longest-first'

    def rule_to_regex(self, rule: dict) -> Pattern:
        """Turns an input string (and the context) from an input/output pair
        into a regular expression pattern"

        The 'in' key is the match.
        The 'context_after' key creates a lookahead.
        The 'context_before' key creates a lookbehind.

        Args:
            rule: A dictionary containing 'in', 'out', 'context_before', and 'context_after' keys

        Raises:
            Exception: This is raised when un-supported regex characters or symbols exist in the rule

        Returns:
            Pattern: returns a regex pattern (re.Pattern)
            bool: returns False if input is null
        """
        # Prevent null input. See, https://github.com/roedoejet/g2p/issues/24
        if not rule['in']:
            LOGGER.warning(
                f'Rule with input \'{rule["in"]}\' and output \'{rule["out"]}\' has no input. This is disallowed. Please check your mapping file for rules with null inputs.')
            return False
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
            in_lang = self.kwargs.get('in_lang', 'und')
            out_lang = self.kwargs.get('out_lang', 'und')
            LOGGER.error(f'Your regex in mapping between {in_lang} and {out_lang} is malformed. \
                    Do you have un-escaped regex characters in your input {inp}, contexts {before}, {after}?')
            raise Exception(
                f'Your regex in mapping between {in_lang} and {out_lang} is malformed. \
                    Do you have un-escaped regex characters in your input {inp}, contexts {before}, {after}?')
        return rule_regex

    def reverse_mappings(self, mapping):
        ''' Reverse the mapping
        '''
        for io in mapping:
            io['in'], io['out'] = io['out'], io['in']
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

    def mapping_to_file(self, output_path: str = GEN_DIR, file_type: str = 'json'):
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
            with open(fn, 'w', encoding='utf8') as f:
                json.dump(filtered, f, indent=4)
        elif file_type == 'csv':
            with open(fn, 'w', encoding='utf8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                for io in filtered:
                    writer.writerow(io)
        else:
            raise exceptions.IncorrectFileType(f'File type {file_type} is invalid.')

    def config_to_file(self, output_path: str = os.path.join(GEN_DIR, 'config.yaml'), mapping_type: str = 'json'):
        ''' Write config to file
        '''
        add_config = False
        if os.path.exists(output_path) and os.path.isfile(output_path):
            LOGGER.warning(f'Adding mapping config to file at {output_path}')
            fn = output_path
            add_config = True
        elif os.path.isdir(output_path):
            fn = os.path.join(output_path, 'config.yaml')
        else:
            LOGGER.warning(f'writing mapping config to file at {output_path}')
            fn = output_path
        template = {"mappings": [
            {
                "language_name": self.kwargs.get('language_name', self.kwargs.get('in_lang', 'und')),
                "display_name": self.kwargs.get('display_name', self.kwargs.get('in_lang', 'und') + " " + self.mapping_type(self.kwargs.get('out_lang', 'und')) + " to " + self.kwargs.get('out_lang', 'und') + " " + self.mapping_type(self.kwargs.get('out_lang', 'und'))),
                "in_lang": self.kwargs.get('in_lang', 'und'),
                "out_lang": self.kwargs.get('out_lang', 'und'),
                "authors": self.kwargs.get('authors', [f'Generated {dt.datetime.now()}']),
                "rule_ordering": self.kwargs.get("rule_ordering", "as-written"),
                "prevent_feeding": self.kwargs.get('prevent_feeding', False),
                "case_sensitive": self.kwargs.get('case_sensitive', True),
                "escape_special": self.kwargs.get('escape_special', False),
                "norm_form": self.kwargs.get('norm_form', "NFD"),
                "reverse": self.kwargs.get('reverse', False),
                "mapping": self.kwargs.get('in_lang', 'und') + "_to_" + self.kwargs.get('out_lang', 'und') + '.' + mapping_type
            }
        ]}
        # If config file exists already, just add the mapping.
        if add_config:
            with open(fn, encoding='utf8') as f:
                existing_data=yaml.safe_load(f.read())
            updated = False
            for i, mapping in enumerate(existing_data['mappings']):
                # if the mapping exists, just update the generation data
                if mapping['in_lang'] == template['mappings'][0]['in_lang'] and mapping['out_lang'] == template['mappings'][0]['out_lang']:
                    existing_data['mappings'][i]['authors'] = template['mappings'][0]['authors']
                    updated = True
                    break
            if not updated:
                existing_data['mappings'].append(template['mappings'][0])
            template=existing_data
        with open(fn, 'w', encoding='utf8') as f:
            yaml.dump(template, f, Dumper=IndentDumper,
                      default_flow_style=False)


if __name__ == '__main__':
    pass
