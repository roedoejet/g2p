"""

Module for all things related to lookup tables

"""

import csv
import os
import unicodedata as ud
import re
from typing import DefaultDict, List, Union
from collections import defaultdict
from itertools import chain
from operator import methodcaller

from openpyxl import load_workbook

from g2p import exceptions
from g2p.mappings.langs import LANGS
from g2p.mappings.langs import __file__ as LANGS_FILE
from g2p.mappings.utils import flatten_abbreviations, unicode_escape
from g2p.log import LOGGER


class Mapping():
    """ Class for lookup tables
    """

    def __init__(self, language, reverse: bool = False, norm_form: str = "NFC",
                 abbreviations: Union[str, DefaultDict[str, List[str]]] = False,
                 case_sensitive: bool = True, **kwargs):
        self.kwargs = kwargs
        self.allowable_norm_forms = ['NFC', 'NKFC', 'NFD', 'NFKD']
        self.norm_form = norm_form
        self.case_sensitive = case_sensitive
        self.path = language
        self.reverse = reverse
        if isinstance(abbreviations, defaultdict) or not abbreviations:
            self.abbreviations = abbreviations
        elif abbreviations:
            self.abbreviations = self.load_abbreviations_from_file(
                abbreviations)

        # Load workbook, either from mapping spreadsheets, or user loaded
        if not isinstance(language, type(None)):
            if isinstance(language, list):
                self.path = 'user supplied data'
                if all('in' in d for d in language) and all('out' in d for d in language):
                    if self.reverse:
                        language = self.reverse_mappings(language)
                    if not all('context_before' in io for io in language):
                        for io in language:
                            if not 'context_before' in io:
                                io['context_before'] = ''
                    if not all('context_after' in io for io in language):
                        for io in language:
                            if not 'context_after' in io:
                                io['context_after'] = ''
                    self.mapping = language
                else:
                    raise exceptions.MalformedMapping()
            elif isinstance(language, dict):
                if not "lang" in language or not "table" in language:
                    raise exceptions.MalformedLookup()
                else:
                    try:
                        lang = [lang for lang in LANGS if lang['name'].strip() ==
                                language['lang'].strip() or lang['code'].strip() == language['lang'].strip()][0]
                        table = [table for table in lang['tables']
                                 if table['name'].strip() == language['table'].strip()][0]
                        self.mapping = self.load_from_file(os.path.join(
                            os.path.dirname(LANGS_FILE), lang['code'], table['table']))
                        if "abbreviations" in table and table['abbreviations']:
                            self.abbreviations = self.load_abbreviations_from_file(os.path.join(
                                os.path.dirname(LANGS_FILE), lang['code'], table['abbreviations']))
                    except KeyError:
                        raise exceptions.MappingMissing(language)
                    except IndexError:
                        raise exceptions.MappingMissing(language)
            else:
                self.mapping = self.load_from_file(language)
        else:
            raise exceptions.MappingMissing(language)

        if self.norm_form in self.allowable_norm_forms:
            for io in self.mapping:
                for k, v in io.items():
                    if isinstance(v, str):
                        io[k] = self.normalize(v)
            if self.abbreviations:
                self.abbreviations = {self.normalize(abb): [self.normalize(
                    x) for x in stands_for] for abb, stands_for in self.abbreviations.items()}
        if self.abbreviations:
            for abb, stands_for in self.abbreviations.items():
                abb_match = re.compile(abb)
                abb_repl = '|'.join(stands_for)
                for io in self.mapping:
                    for key in io.keys():
                        if re.search(abb_match, io[key]):
                            io[key] = re.sub(abb_match, abb_repl, io[key])
        if not self.case_sensitive:
            self.lower_mappings(self.mapping)

    def __len__(self):
        return len(self.mapping)

    def __call__(self):
        return self.mapping

    def __iter__(self):
        return iter(self.mapping)

    def normalize(self, inp: str):
        ''' Normalize to NFC(omposed) or NFD(ecomposed).
            Also, find any Unicode Escapes & decode 'em!
        '''
        if self.norm_form not in self.allowable_norm_forms:
            raise exceptions.InvalidNormalization(self.normalize)
        else:
            normalized = ud.normalize(self.norm_form, unicode_escape(inp))
            if normalized != inp:
                LOGGER.info(
                    'The string %s was normalized to %s using the %s standard and by decoding any Unicode escapes. Note that this is not necessarily the final stage of normalization.',
                    inp, normalized, self.norm_form)
            return normalized

    def reverse_mappings(self, mapping):
        ''' Reverse the table
        '''
        for io in mapping:
            io['in'], io['out'] = io['out'], io['in']
        return mapping

    def lower_mappings(self, mapping):
        ''' Lower the table
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

    def load_abbreviations_from_file(self, path):
        ''' Helper method to load abbreviations from file.
        '''
        if path.endswith('csv'):
            abbs = []
            with open(path, encoding='utf8') as f:
                reader = csv.reader(f)
                abbs = flatten_abbreviations(reader)
        else:
            raise exceptions.IncorrectFileType(
                '''Sorry, abbreviations must be stored as CSV files.
                You provided the following: %s''' % path)
        return abbs

    def load_from_file(self, path):
        ''' Helper method to load table from file.
        '''
        if path.endswith('csv'):
            return self.load_from_csv(path)
        elif path.endswith('xlsx'):
            return self.load_from_workbook(path)

    def load_from_csv(self, language):
        ''' Parse table from csv
        '''
        work_sheet = []
        with open(language, encoding='utf8') as f:
            reader = csv.reader(f)
            for line in reader:
                work_sheet.append(line)
        # Create wordlist
        mapping = []
        # Loop through rows in worksheet, create if statements for different columns
        # and append mappings to self.mapping.
        for entry in work_sheet:
            new_io = {"in": "", "out": "",
                      "context_before": "", "context_after": ""}
            new_io['in'] = entry[0]
            new_io['out'] = entry[1]
            try:
                new_io['context_before'] = entry[2]
            except IndexError:
                new_io['context_before'] = ''
            try:
                new_io['context_after'] = entry[3]
            except IndexError:
                new_io['context_after'] = ''
            for k in new_io:
                if isinstance(new_io[k], float) or isinstance(new_io[k], int):
                    new_io[k] = str(new_io[k])

            mapping.append(new_io)

        if self.reverse:
            mapping = self.reverse_mappings(mapping)

        return mapping

    def load_from_workbook(self, language):
        ''' Parse table from Excel workbook
        '''
        work_book = load_workbook(language)
        work_sheet = work_book.active
        # Create wordlist
        mapping = []
        # Loop through rows in worksheet, create if statements for different columns
        # and append mappings to self.mapping.
        for entry in work_sheet:
            new_io = {"in": "", "out": "",
                      "context_before": "", "context_after": ""}
            for col in entry:
                if col.column == 'A':
                    value = col.value
                    if isinstance(value, (float, int)):
                        value = str(value)
                    new_io["in"] = value
                if col.column == 'B':
                    value = col.value
                    if isinstance(value, (float, int)):
                        value = str(value)
                    new_io["out"] = value
                if col.column == 'C':
                    if col.value is not None:
                        value = col.value
                        if isinstance(value, (float, int)):
                            value = str(value)
                        new_io["context_before"] = value
                if col.column == 'D':
                    if col.value is not None:
                        value = col.value
                        if isinstance(value, (float, int)):
                            value = str(value)
                        new_io["context_after"] = value
            mapping.append(new_io)

        if self.reverse:
            mapping = self.reverse_mappings(mapping)

        return mapping
