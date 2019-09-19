"""

Utilities used by other classes

"""
import os
import csv
from collections import defaultdict
from typing import List
import regex as re
import json
from copy import deepcopy
from pathlib import Path
import datetime as dt
import yaml

import unicodedata as ud

from openpyxl import load_workbook
from typing import Dict

from g2p import exceptions
from g2p.log import LOGGER
from g2p.mappings import langs

GEN_DIR = os.path.join(os.path.dirname(langs.__file__), 'generated')
GEN_CONFIG = os.path.join(GEN_DIR, 'config.yaml')

def flatten_abbreviations(data):
    ''' Turn a CSV-sourced list of lists into a flattened DefaultDict
    '''
    default_dict = defaultdict(list)
    for line in data:
        if line[0]:
            default_dict[line[0]].extend([l for l in line[1:] if l])
    return default_dict


def expand_abbreviations(data):
    ''' Exapand a flattened DefaultDict into a CSV-formatted list of lists
    '''
    lines = []
    if data:
        for key in data.keys():
            line = [key]
            for col in data[key]:
                line.append(col)
            lines.append(line)
    if not lines:
        while len(lines) < 10:
            lines.append(['', '', '', '', '', ''])
    return lines

def normalize(inp: str, norm_form: str):
    ''' Normalize to NFC(omposed) or NFD(ecomposed).
        Also, find any Unicode Escapes & decode 'em!
    '''
    if norm_form not in ['NFC', 'NFD', 'NKFC', 'NKFD']:
        raise exceptions.InvalidNormalization(normalize)
    else:
        normalized = ud.normalize(norm_form, unicode_escape(inp))
        if normalized != inp:
            LOGGER.info(
                'The string %s was normalized to %s using the %s standard and by decoding any Unicode escapes. Note that this is not necessarily the final stage of normalization.',
                inp, normalized, norm_form)
        return normalized

def unicode_escape(text):
    ''' Find any escaped characters and turn them into codepoints
    '''
    return re.sub(r"""\\(u[0-9A-Fa-f]{4}|U[0-9A-Fa-f]{6})""", escape_to_codepoint, text)


def escape_to_codepoint(match):
    ''' Turn escape into codepoint
    '''
    hex_codepoint = match.group(1)[1:]
    return chr(int(hex_codepoint, base=16))


def create_fixed_width_lookbehind(pattern):
    '''Turn all characters into fixed width lookbehinds
    '''
    return re.sub(re.compile(r"""(?<=\(?)[\p{L}\p{M}|]+(?=\)?)""", re.U),
                  pattern_to_fixed_width_lookbehinds, pattern)


def pattern_to_fixed_width_lookbehinds(match):
    ''' Python must have fixed-width lookbehinds.
    '''
    pattern = match.group()
    pattern = sorted(pattern.split('|'), key=len, reverse=True)
    current_len = len(pattern[0])
    all_lookbehinds = []
    current_list = []
    for item in pattern:
        if len(item) == current_len:
            current_list.append(item)
        else:
            current_len = len(item)
            all_lookbehinds.append(current_list)
            current_list = [item]
        if pattern.index(item) == len(pattern) - 1:
            all_lookbehinds.append(current_list)
    all_lookbehinds = [f"(?<={'|'.join(items)})" for items in all_lookbehinds]
    return '(' + '|'.join(all_lookbehinds) + ')'


def load_from_workbook(language):
    ''' Parse mapping from Excel workbook
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

    return mapping


def load_from_csv(language):
    ''' Parse mapping from csv
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

    return mapping


def load_from_file(path: str) -> list:
    ''' Helper method to load mapping from file.
    '''
    if path.endswith('csv'):
        mapping = load_from_csv(path)
    elif path.endswith('xlsx'):
        mapping = load_from_workbook(path)
    elif path.endswith('json'):
        with open(path) as f:
            mapping = json.load(f)
    return validate(mapping)


def load_mapping_from_path(path_to_mapping_config, index=0):
    ''' Loads a mapping from a path, if there is more than one mapping, then it loads based on the int
        provided to the 'index' argument. Default is 0.
    '''
    path = Path(path_to_mapping_config)
    # If path leads to actual mapping config
    if path.exists() and (path.suffix.endswith('yml') or path.suffix.endswith('yaml')):
        # safe load it
        with open(path) as f:
            mapping = yaml.safe_load(f)
        # If more than one mapping in the mapping config
        if 'mappings' in mapping:
            try:
                LOGGER.info('Loading mapping from %s between "%s" and "%s" at index %s', path_to_mapping_config,
                            mapping['mappings'][index]['in_lang'], mapping['mappings'][index]['out_lang'], index)
                mapping = mapping['mappings'][index]
            except KeyError:
                LOGGER.warning(
                    'An index of %s was provided for the mapping %s but that index does not exist in the mapping. Please check your mapping.', index, path_to_mapping_config)
        # Log the warning if an Index other than 0 was provided for a mapping config with a single mapping.
        elif index != 0:
            LOGGER.warning(
                'An index of %s was provided for the mapping %s but that index does not exist in the mapping. Please check your mapping.', index, path_to_mapping_config)
        # try to load the data from the mapping data file
        if 'mapping' in mapping:
            mapping['mapping_data'] = load_from_file(
                os.path.join(path.parent, mapping['mapping']))
        else:
            # Is "mapping" key missing?
            raise exceptions.MalformedMapping
        # load any abbreviations
        if 'abbreviations' in mapping:
            mapping['abbreviations_data'] = load_abbreviations_from_file(
                os.path.join(path.parent, mapping['abbreviations']))
        return mapping
    else:
        raise FileNotFoundError


def validate(mapping):
    try:
        for io in mapping:
            if not 'context_before' in io:
                io['context_before'] = ''
            if not 'context_after' in io:
                io['context_after'] = ''
        valid = all('in' in d for d in mapping) and all(
            'out' in d for d in mapping)
        if not valid:
            raise exceptions.MalformedMapping()
        return mapping
    except TypeError:
        # The JSON probably is not just a list (ie could be legacy readalongs format) TODO: proper exception handling
        raise exceptions.MalformedMapping()


def escape_special_characters(to_escape: Dict[str, str]) -> Dict[str, str]:
    for k, v in to_escape.items():
        if isinstance(v, str):
            escaped = re.escape(v)
        else:
            escaped = v
        if escaped != v:
            LOGGER.info(
                f"Escaped special characters in '{v}' with '{escaped}''. Set 'escape_special' to False in your Mapping configuration to disable this.")
        to_escape[k] = escaped
    return to_escape


def load_abbreviations_from_file(path):
    ''' Helper method to load abbreviations from file.
    '''
    if path.endswith('csv'):
        abbs = []
        with open(path, encoding='utf8') as f:
            reader = csv.reader(f)
            abbs = flatten_abbreviations(reader)
    else:
        raise exceptions.IncorrectFileType(f'Sorry, abbreviations must be stored as CSV files. You provided the following: {path}')
    return abbs

def generate_config(in_lang, out_lang, in_display_name, out_display_name):
    if is_ipa(in_lang):
        in_type = 'IPA'
    elif is_xsampa(in_lang):
        in_type = 'XSAMPA'
    elif is_dummy(in_lang):
        in_type = 'dummy'
    else:
        in_type = 'custom'

    if is_ipa(out_lang):
        out_type = 'IPA'
    elif is_xsampa(out_lang):
        out_type = 'XSAMPA'
    elif is_dummy(out_lang):
        out_type = 'dummy'
    else:
        out_type = 'custom'
        
    mapping_fn = f'{in_lang}_to_{out_lang}.json'
    config = {
        'display_name': f"{in_display_name} {in_type} to {out_display_name} {out_type}",
        'mapping': mapping_fn,
        'in_lang': in_lang,
        'out_lang': out_lang,
        'language_name': in_display_name,
        'author': f"Generated {dt.datetime.now()}"
    }
    return config

def write_generated_mapping_to_file(config: dict, mapping: List[dict]):
    # read config
    with open(GEN_CONFIG, 'r') as f:
        data = yaml.safe_load(f)
    map_output_path = os.path.join(GEN_DIR, config['mapping'])
    # write mapping
    if os.path.exists(map_output_path):
        LOGGER.info(f"Overwriting file at {map_output_path}")
    with open(map_output_path, 'w') as f:
        json.dump(mapping, f, indent=4)
    data = deepcopy(data)
    cfg_exists = bool([x for x in data['mappings'] if x['in_lang']
                       == config['in_lang'] and x['out_lang'] == config['out_lang']])
    # add new mapping if no mappings are generated yet
    if not data['mappings']:
        data['mappings'] = [config]
    # add new mapping if it doesn't exist yet
    elif not cfg_exists:
        data['mappings'].append(config)
        # rewrite config
        with open(GEN_CONFIG, 'w') as f:
            yaml.dump(data, f, Dumper=IndentDumper, default_flow_style=False)
    elif cfg_exists:
        for i, cfg in enumerate(data['mappings']):
            if cfg['in_lang'] == config['in_lang'] and cfg['out_lang'] == config['out_lang']:
                data['mappings'][i] = config
                # rewrite config
                with open(GEN_CONFIG, 'w') as f:
                    yaml.dump(data, f, Dumper=IndentDumper,
                              default_flow_style=False)
                break
    else:
        LOGGER.warn(
            f"Not writing generated files because a non-generated mapping from {config['in_lang']} to {config['out_lang']} already exists.")

def is_ipa(lang: str) -> bool:
    pattern = re.compile('[-_]?ipa$')
    return bool(re.search(pattern, lang))

def is_xsampa(lang: str) -> bool:
    pattern = re.compile('[-_]?x(-?)sampa$')
    return bool(re.search(pattern, lang))

def is_dummy(lang: str) -> bool:
    return lang == 'dummy'

class IndentDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(IndentDumper, self).increase_indent(flow, False)

    def ignore_aliases(self, *args):
        return True
