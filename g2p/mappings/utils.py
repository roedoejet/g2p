"""

Utilities used by other classes

"""
import csv
import json
import os
import unicodedata as ud
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Dict

import regex as re
import yaml

from g2p import exceptions
from g2p.log import LOGGER
from g2p.mappings import langs

GEN_DIR = os.path.join(os.path.dirname(langs.__file__), "generated")
GEN_CONFIG = os.path.join(GEN_DIR, "config.yaml")


def flatten_abbreviations(data):
    """ Turn a CSV-sourced list of lists into a flattened DefaultDict
    """
    default_dict = defaultdict(list)
    for line in data:
        if line[0]:
            default_dict[line[0]].extend([l for l in line[1:] if l])
    return default_dict


def expand_abbreviations(data):
    """ Exapand a flattened DefaultDict into a CSV-formatted list of lists
    """
    lines = []
    if data:
        for key in data.keys():
            line = [key]
            for col in data[key]:
                line.append(col)
            lines.append(line)
    if not lines:
        while len(lines) < 10:
            lines.append(["", "", "", "", "", ""])
    return lines


def normalize(inp: str, norm_form: str):
    """ Normalize to NFC(omposed) or NFD(ecomposed).
        Also, find any Unicode Escapes & decode 'em!
    """
    if norm_form not in ["none", "NFC", "NFD", "NFKC", "NFKD"]:
        raise exceptions.InvalidNormalization(normalize)
    elif norm_form is None or norm_form == "none":
        return unicode_escape(inp)
    else:
        normalized = ud.normalize(norm_form, unicode_escape(inp))
        if normalized != inp:
            LOGGER.debug(
                "The string %s was normalized to %s using the %s standard and by decoding any Unicode escapes. "
                "Note that this is not necessarily the final stage of normalization.",
                inp,
                normalized,
                norm_form,
            )
        return normalized


def unicode_escape(text):
    """ Find any escaped characters and turn them into codepoints
    """
    return re.sub(r"""\\(u[0-9A-Fa-f]{4}|U[0-9A-Fa-f]{6})""", escape_to_codepoint, text)


def escape_to_codepoint(match):
    """ Turn escape into codepoint
    """
    hex_codepoint = match.group(1)[1:]
    return chr(int(hex_codepoint, base=16))


def create_fixed_width_lookbehind(pattern):
    """Turn all characters into fixed width lookbehinds
    """
    return re.sub(
        re.compile(
            r"""
    (?<=\(?)              # lookbehind
    [\\\[\]\p{L}\p{M}|.]+  # match any number of Unicode characters and diacritics, plus square brackets, and backslash so patterns like \b can be used
    (?=\)?)               # lookahead
    """,
            re.U | re.VERBOSE,
        ),
        pattern_to_fixed_width_lookbehinds,
        pattern,
    )


def pattern_to_fixed_width_lookbehinds(match):
    """ Python must have fixed-width lookbehinds.
    """
    pattern = match.group()
    pattern = sorted(pattern.split("|"), key=len, reverse=True)
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
    return "(" + "|".join(all_lookbehinds) + ")"


def load_from_workbook(language):
    """ Parse mapping from Excel workbook
    """
    from openpyxl import load_workbook  # Expensive import, do it only when needed

    work_book = load_workbook(language)
    work_sheet = work_book.active
    # Create wordlist
    mapping = []
    # Loop through rows in worksheet, create if statements for different columns
    # and append mappings to self.mapping.
    for entry in work_sheet:
        new_io = {"in": "", "out": "", "context_before": "", "context_after": ""}
        for col in entry:
            if col.column == "A" or col.column == 1:
                value = col.value
                if isinstance(value, (float, int)):
                    value = str(value)
                new_io["in"] = value
            if col.column == "B" or col.column == 2:
                value = col.value
                if isinstance(value, (float, int)):
                    value = str(value)
                new_io["out"] = value
            if col.column == "C" or col.column == 3:
                if col.value is not None:
                    value = col.value
                    if isinstance(value, (float, int)):
                        value = str(value)
                    new_io["context_before"] = value
            if col.column == "D" or col.column == 4:
                if col.value is not None:
                    value = col.value
                    if isinstance(value, (float, int)):
                        value = str(value)
                    new_io["context_after"] = value
        mapping.append(new_io)

    return mapping


def load_from_csv(language, delimiter=","):
    """ Parse mapping from csv
    """
    work_sheet = []
    with open(language, encoding="utf8") as f:
        reader = csv.reader(f, delimiter=delimiter)
        for line in reader:
            work_sheet.append(line)
    # Create wordlist
    mapping = []
    # Loop through rows in worksheet, create if statements for different columns
    # and append mappings to self.mapping.
    for entry in work_sheet:
        new_io = {"in": "", "out": "", "context_before": "", "context_after": ""}
        if len(entry) == 0:
            # Just ignore empty lines in the CSV file
            continue

        if len(entry) == 1:
            raise exceptions.MalformedMapping(
                'Entry {} in mapping {} has no "out" value.'.format(entry, language)
            )

        new_io["in"] = entry[0]
        new_io["out"] = entry[1]
        try:
            new_io["context_before"] = entry[2]
        except IndexError:
            new_io["context_before"] = ""
        try:
            new_io["context_after"] = entry[3]
        except IndexError:
            new_io["context_after"] = ""
        for k in new_io:
            if isinstance(new_io[k], (float, int)):
                new_io[k] = str(new_io[k])
        mapping.append(new_io)

    return mapping


def load_from_file(path: str) -> list:
    """ Helper method to load mapping from file.
    """
    if path.endswith("csv"):
        mapping = load_from_csv(path, ",")
    elif path.endswith("tsv"):
        mapping = load_from_csv(path, "\t")
    elif path.endswith("psv"):
        mapping = load_from_csv(path, "|")
    elif path.endswith("xlsx"):
        mapping = load_from_workbook(path)
    elif path.endswith("json"):
        with open(path, encoding="utf8") as f:
            mapping = json.load(f)
    else:
        raise exceptions.IncorrectFileType(
            f"File {path} is not a valid mapping filetype."
        )
    return validate(mapping, path)


def load_mapping_from_path(path_to_mapping_config, index=0):
    """ Loads a mapping from a path, if there is more than one mapping, then it loads based on the int
        provided to the 'index' argument. Default is 0.
    """
    path = Path(path_to_mapping_config)
    # If path leads to actual mapping config
    if path.exists() and (path.suffix.endswith("yml") or path.suffix.endswith("yaml")):
        # safe load it
        with open(path, encoding="utf8") as f:
            mapping = yaml.safe_load(f)
        # If more than one mapping in the mapping config
        if "mappings" in mapping:
            try:
                LOGGER.debug(
                    'Loading mapping from %s between "%s" and "%s" at index %s',
                    path_to_mapping_config,
                    mapping["mappings"][index].get("in_lang", "und"),
                    mapping["mappings"][index].get("out_lang", "und"),
                    index,
                )
                mapping = mapping["mappings"][index]
            except KeyError:
                LOGGER.warning(
                    "An index of %s was provided for the mapping %s but that index does not exist in the mapping. "
                    "Please check your mapping.",
                    index,
                    path_to_mapping_config,
                )
        # Log the warning if an Index other than 0 was provided for a mapping config with a single mapping.
        elif index != 0:
            LOGGER.warning(
                "An index of %s was provided for the mapping %s but that index does not exist in the mapping. "
                "Please check your mapping.",
                index,
                path_to_mapping_config,
            )
        # try to load the data from the mapping data file
        if "mapping" in mapping:
            try:
                mapping["mapping_data"] = load_from_file(
                    os.path.join(path.parent, mapping["mapping"])
                )
            except (OSError, exceptions.IncorrectFileType) as e:
                raise exceptions.MalformedMapping(
                    f"Cannot load mapping data file specified in {path}: {e}"
                ) from e
        elif mapping.get("type", "") == "unidecode":
            # This mapping is not implemented as a regular mapping, but as custom software
            pass
        else:
            # Is "mapping" key missing?
            raise exceptions.MalformedMapping(
                'Key "mapping:" missing from a mapping in {}.'.format(path)
            )
        # load any abbreviations
        if "abbreviations" in mapping:
            try:
                mapping["abbreviations_data"] = load_abbreviations_from_file(
                    os.path.join(path.parent, mapping["abbreviations"])
                )
            except (OSError, exceptions.IncorrectFileType) as e:
                raise exceptions.MalformedMapping(
                    f"Cannot load abbreviations data file specified in {path}: {e}"
                ) from e
        return mapping
    else:
        raise FileNotFoundError


def find_mapping(in_lang: str, out_lang: str) -> list:
    """ Given an input and output, find a mapping to get between them.
    """
    for mapping in langs.MAPPINGS_AVAILABLE:
        map_in_lang = mapping.get("in_lang", "")
        map_out_lang = mapping.get("out_lang", "")
        if map_in_lang == in_lang and map_out_lang == out_lang:
            return deepcopy(mapping)
    raise exceptions.MappingMissing(in_lang, out_lang)


def validate(mapping, path):
    try:
        for io in mapping:
            if not "context_before" in io:
                io["context_before"] = ""
            if not "context_after" in io:
                io["context_after"] = ""
        valid = all("in" in d for d in mapping) and all("out" in d for d in mapping)
        if not valid:
            raise exceptions.MalformedMapping(
                'Missing "in" or "out" in an entry in {}.'.format(path)
            )
        return mapping
    except TypeError as e:
        # The JSON probably is not just a list (ie could be legacy readalongs format)
        # TODO: proper exception handling
        raise exceptions.MalformedMapping(
            "Formatting error in mapping in {}.".format(path)
        ) from e


def escape_special_characters(to_escape: Dict[str, str]) -> Dict[str, str]:
    for k, v in to_escape.items():
        if isinstance(v, str):
            escaped = re.escape(v)
        else:
            escaped = v
        if escaped != v:
            LOGGER.debug(
                f"Escaped special characters in '{v}' with '{escaped}''. Set 'escape_special' "
                "to False in your Mapping configuration to disable this."
            )
        to_escape[k] = escaped
    return to_escape


def load_abbreviations_from_file(path):
    """ Helper method to load abbreviations from file.
    """
    if path.endswith("csv"):
        abbs = []
        with open(path, encoding="utf8") as f:
            reader = csv.reader(f, delimiter=",")
            abbs = flatten_abbreviations(reader)
    elif path.endswith("tsv"):
        abbs = []
        with open(path, encoding="utf8") as f:
            reader = csv.reader(f, delimiter="\t")
            abbs = flatten_abbreviations(reader)
    elif path.endswith("psv"):
        abbs = []
        with open(path, encoding="utf8") as f:
            reader = csv.reader(f, delimiter="|")
            abbs = flatten_abbreviations(reader)
    else:
        raise exceptions.IncorrectFileType(
            f"Sorry, abbreviations must be stored as CSV/TSV/PSV files. You provided the following: {path}"
        )
    return abbs


def is_ipa(lang: str) -> bool:
    pattern = re.compile("[-_]?ipa$")
    return bool(re.search(pattern, lang))


def is_xsampa(lang: str) -> bool:
    pattern = re.compile("[-_]?x(-?)sampa$")
    return bool(re.search(pattern, lang))


def is_dummy(lang: str) -> bool:
    return lang == "dummy"


class IndentDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)

    def ignore_aliases(self, *args):
        return True


def merge_if_same_label(lst_of_dicts, text_key, label_key):
    results = []
    current_item = None
    for dct in lst_of_dicts:
        if label_key not in dct:
            dct[label_key] = None
        if not current_item:
            current_item = deepcopy(dct)
        elif dct[label_key] == current_item[label_key]:
            current_item[text_key] += dct[text_key]
        else:
            results.append(current_item)
            current_item = deepcopy(dct)
    if current_item:
        results.append(current_item)
    return results


CATEGORIES = {
    "Cc": "other",  # Other, Control
    "Cf": "other",  # Other, Format
    "Cn": "other",  # Other, Not Assigned (no characters in the file have this property)
    "Co": "letter",  # Other, Private Use
    "Cs": "other",  # Other, Surrogate
    "LC": "letter",  # Letter, Cased
    "Ll": "letter",  # Letter, Lowercase
    "Lm": "letter",  # Letter, Modifier
    "Lo": "letter",  # Letter, Other
    "Lt": "letter",  # Letter, Titlecase
    "Lu": "letter",  # Letter, Uppercase
    "Mc": "diacritic",  # Mark, Spacing Combining
    "Me": "diacritic",  # Mark, Enclosing
    "Mn": "diacritic",  # Mark, Nonspacing
    "Nd": "number",  # Number, Decimal Digit
    "Nl": "number",  # Number, Letter
    "No": "number",  # Number, Other
    "Pc": "punctuation",  # Punctuation, Connector
    "Pd": "punctuation",  # Punctuation, Dash
    "Pe": "punctuation",  # Punctuation, Close
    "Pf": "punctuation",  # Punctuation, Final quote (may behave like Ps or Pe depending on usage)
    "Pi": "punctuation",  # Punctuation, Initial quote (may behave like Ps or Pe depending on usage)
    "Po": "punctuation",  # Punctuation, Other
    "Ps": "punctuation",  # Punctuation, Open
    "Sc": "symbol",  # Symbol, Currency
    "Sk": "symbol",  # Symbol, Modifier
    "Sm": "symbol",  # Symbol, Math
    "So": "symbol",  # Symbol, Other
    "Zl": "whitespace",  # Separator, Line
    "Zp": "whitespace",  # Separator, Paragraph
    "Zs": "whitespace",  # Separator, Space
}


def get_unicode_category(c):
    """ Maps a character to one of [ "letter", "number", "diacritic", "punctuation",
        "symbol", "whitespace", "other"] """
    cat = ud.category(c)
    assert cat in CATEGORIES
    return CATEGORIES[cat]


class CompactJSONMappingEncoder(json.JSONEncoder):
    """A JSON Encoder that puts individual rules on a single line.

    This way, it's easy to look at a generated mapping visually.

    This code is adapted from https://stackoverflow.com/questions/16264515/json-dumps-custom-formatting
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.indentation_level = 0

    def encode(self, obj):
        if isinstance(obj, dict) and "in" in obj and "out" in obj:
            # Compact, single-line output for the individual rules in the mapping
            return json.dumps(obj, ensure_ascii=self.ensure_ascii)
        elif isinstance(obj, (list, tuple)):
            self.indentation_level += 1
            output = [self.indent_str + self.encode(el) for el in obj]
            self.indentation_level -= 1
            return "[\n" + ",\n".join(output) + "\n" + self.indent_str + "]"
        elif isinstance(obj, dict):
            self.indentation_level += 1
            output = [self.indent_str + f"{json.dumps(k)}: {self.encode(v)}" for k, v in obj.items()]
            self.indentation_level -= 1
            return "{\n" + ",\n".join(output) + "\n" + self.indent_str + "}"
        else:
            return json.dumps(obj, ensure_ascii=self.ensure_ascii)

    @property
    def indent_str(self) -> str:
        return " " * self.indentation_level * self.indent

    def iterencode(self, obj, **kwargs):
        return self.encode(obj)
