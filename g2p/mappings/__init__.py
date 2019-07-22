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
                 abbreviations: Union[str, DefaultDict[str, List[str]]] = False, **kwargs):
        self.kwargs = kwargs
        self.allowable_norm_forms = ['NFC', 'NKFC', 'NFD', 'NFKD']
        self.norm_form = norm_form
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
                    if not all('context_before' in cor for cor in language):
                        for cor in language:
                            if not 'context_before' in cor:
                                cor['context_before'] = ''
                    if not all('context_after' in cor for cor in language):
                        for cor in language:
                            if not 'context_after' in cor:
                                cor['context_after'] = ''
                    self.cor_list = language
                else:
                    raise exceptions.MalformedMapping()
            elif isinstance(language, object):
                if not "lang" in language or not "table" in language:
                    raise exceptions.MalformedLookup()
                else:
                    try:
                        lang = [lang for lang in LANGS if lang['name'].strip() ==
                                language['lang'].strip() or lang['code'].strip() == language['lang'].strip()][0]
                        table = [table for table in lang['tables']
                                 if table['name'].strip() == language['table'].strip()][0]
                        self.cor_list = self.load_from_file(os.path.join(
                            os.path.dirname(LANGS_FILE), lang['code'], table['table']))
                        if "abbreviations" in table and table['abbreviations']:
                            self.abbreviations = self.load_abbreviations_from_file(os.path.join(
                                os.path.dirname(LANGS_FILE), lang['code'], table['abbreviations']))
                    except KeyError:
                        raise exceptions.MappingMissing(language)
                    except IndexError:
                        raise exceptions.MappingMissing(language)
            else:
                self.cor_list = self.load_from_file(language)
        else:
            raise exceptions.MappingMissing(language)

        if self.norm_form in self.allowable_norm_forms:
            for cor in self.cor_list:
                for k, v in cor.items():
                    cor[k] = self.normalize(v)
            if self.abbreviations:
                self.abbreviations = {self.normalize(abb): [self.normalize(
                    x) for x in stands_for] for abb, stands_for in self.abbreviations.items()}
        if self.abbreviations:
            for abb, stands_for in self.abbreviations.items():
                abb_match = re.compile(abb)
                abb_repl = '|'.join(stands_for)
                for cor in self.cor_list:
                    for key in cor.keys():
                        if re.search(abb_match, cor[key]):
                            cor[key] = re.sub(abb_match, abb_repl, cor[key])

    def __len__(self):
        return len(self.cor_list)

    def __call__(self):
        return self.cor_list

    def __iter__(self):
        return iter(self.cor_list)

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

    def reverse_mappings(self, cor_list):
        ''' Reverse the table
        '''
        for cor in cor_list:
            cor['in'], cor['out'] = cor['out'], cor['in']
        return cor_list

    def add_abbreviations(self, abbs, mappings):
        ''' Return abbreviated forms, given a list of abbreviations.

        {'in': 'a', 'out': 'b', 'context_before': 'V', 'context_after': '' }
        {'abbreviation': 'V', 'stands_for': ['a','b','c']}
        ->
        {'in': 'a', 'out': 'b', 'context_before': 'a|b|c', 'context_after': ''}
        '''
        for abb in abbs:
            for cor in mappings:
                for key in cor.keys():
                    if cor[key] == abb['abbreviation']:
                        cor[key] = abb['stands_for']
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
        cor_list = []
        # Loop through rows in worksheet, create if statements for different columns
        # and append mappings to cor_list.
        for entry in work_sheet:
            new_cor = {"in": "", "out": "", "context_before": "", "context_after": ""}
            new_cor['in'] = entry[0]
            new_cor['out'] = entry[1]
            try:
                new_cor['context_before'] = entry[2]
            except IndexError:
                new_cor['context_before'] = ''
            try:
                new_cor['context_after'] = entry[3]
            except IndexError:
                new_cor['context_after'] = ''
            for k in new_cor:
                if isinstance(new_cor[k], float) or isinstance(new_cor[k], int):
                    new_cor[k] = str(new_cor[k])

            cor_list.append(new_cor)

        if self.reverse:
            cor_list = self.reverse_mappings(cor_list)

        return cor_list

    def load_from_workbook(self, language):
        ''' Parse table from Excel workbook
        '''
        work_book = load_workbook(language)
        work_sheet = work_book.active
        # Create wordlist
        cor_list = []
        # Loop through rows in worksheet, create if statements for different columns
        # and append mappings to cor_list.
        for entry in work_sheet:
            new_cor = {"in": "", "out": "", "context_before": "", "context_after": ""}
            for col in entry:
                if col.column == 'A':
                    value = col.value
                    if isinstance(value, (float, int)):
                        value = str(value)
                    new_cor["in"] = value
                if col.column == 'B':
                    value = col.value
                    if isinstance(value, (float, int)):
                        value = str(value)
                    new_cor["out"] = value
                if col.column == 'C':
                    if col.value is not None:
                        value = col.value
                        if isinstance(value, (float, int)):
                            value = str(value)
                        new_cor["context_before"] = value
                if col.column == 'D':
                    if col.value is not None:
                        value = col.value
                        if isinstance(value, (float, int)):
                            value = str(value)
                        new_cor["context_after"] = value
            cor_list.append(new_cor)

        if self.reverse:
            cor_list = self.reverse_mappings(cor_list)

        return cor_list
