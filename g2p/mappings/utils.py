"""

Utilities used by other classes

"""

import csv
import json
import os
import unicodedata as ud
from bisect import bisect_left
from collections import defaultdict
from copy import deepcopy
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Pattern, Tuple, TypeVar, Union

import regex as re
import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    DirectoryPath,
    Field,
    ValidationInfo,
    field_serializer,
    field_validator,
    model_validator,
)

from g2p import exceptions
from g2p.log import LOGGER
from g2p.mappings import langs

GEN_DIR = os.path.join(os.path.dirname(langs.__file__), "generated")
GEN_CONFIG = os.path.join(GEN_DIR, "config-g2p.yaml")


class Rule(BaseModel):
    # We can't just use "in" because it's disallowed by Python
    rule_input: str = Field(alias="in")
    """The character(s) to convert"""

    rule_output: str = Field(alias="out")
    """What to convert the 'in' characters to"""

    context_before: str = ""
    """The context before 'in' required for the rule to apply"""

    context_after: str = ""
    """The context after 'in' required for the rule to apply"""

    prevent_feeding: bool = False
    """Whether to prevent the rule from feeding other rules"""

    match_pattern: Optional[Pattern] = None
    """An automatically generated match_pattern based on the rule_input, context_before and context_after"""

    intermediate_form: Optional[str] = None
    """An optional intermediate form. Should be automatically generated only when prevent_feeding is True"""

    comment: Optional[str] = None
    """An optional comment about the rule."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    def export_to_dict(
        self, exclude=None, exclude_none=True, exclude_defaults=True, by_alias=True
    ):
        """All the options for exporting are tedious to keep track of so this is a helper function"""
        if exclude is None:
            exclude = {"match_pattern": True, "intermediate_form": True}
        return self.model_dump(
            exclude=exclude,
            exclude_none=exclude_none,
            exclude_defaults=exclude_defaults,
            by_alias=by_alias,
        )


def expand_abbreviations(data: str, abbs: Dict[str, List[str]], recursion_depth=0):
    """Given a string, expand any abbreviations in it recursively

    Args:
        data (str): a string that may or may not contain recursive 'abbreviations'
    """
    if recursion_depth > 10:
        raise exceptions.RecursionError(
            "Too many levels of recursion in your abbreviation expansion. Check your abbreviations for circular references."
        )
    for abb, stands_for in sorted(abbs.items(), key=lambda x: len(x[0]), reverse=True):
        abb_match = re.compile(abb)
        abb_repl = "|".join(stands_for)
        if re.search(abb_match, data):
            data = re.sub(abb_match, abb_repl, data)
            recursion_depth += 1
            data = expand_abbreviations(data, abbs, recursion_depth=recursion_depth)
            break
    return data


def flatten_abbreviations_format(data):
    """Turn a CSV-sourced list of lists into a flattened DefaultDict"""
    default_dict = defaultdict(list)
    for line in data:
        if line[0]:
            default_dict[line[0]].extend(
                [definition for definition in line[1:] if definition]
            )
    return default_dict


def expand_abbreviations_format(data):
    """Expand a flattened DefaultDict into a CSV-formatted list of lists"""
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
    """Normalize to NFC(omposed) or NFD(ecomposed).

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


# compose_indices is generic because we would like to propagate the
# type of its second input, in the case where we *know* there will not
# be None (NFC and NFD conversions)
IntOrOptionalInt = TypeVar("IntOrOptionalInt", bound=Union[int, None])


def compose_indices(
    indices1: List[Tuple[int, int]], indices2: List[Tuple[int, IntOrOptionalInt]]
) -> List[Tuple[int, IntOrOptionalInt]]:
    """Compose indices1 + indices2 into direct arcs from the inputs of indices1
    to the outputs of indices 2.

    E.g., [(0,1), (1,4)] composed with [(0,0), (1,2), (1,3), (4,2)] is
    [(0,2), (0,3), (1,2)]
    """
    # for O(1) lookup of arcs leaving indices2
    indices2_as_dict = defaultdict(dict)  # type: ignore
    for a, b in indices2:
        indices2_as_dict[a][b] = True  # we're using dict as an ordered set...

    result = ((a, c) for a, b in indices1 for c in indices2_as_dict[b].keys())
    return list(dict.fromkeys(result).keys())  # return a deduplicated list


def normalize_to_NFD_with_indices(
    inp: str, norm_form: str
) -> Tuple[str, List[Tuple[int, int]]]:
    """Normalize to NFD and return the indices mapping input to output characters"""
    assert norm_form in ("NFD", "NFKD")
    result = ""
    indices = []
    for i, c in enumerate(inp):
        c_nfd = ud.normalize(norm_form, c)
        result_pos = len(result)
        result += c_nfd
        indices.extend([(i, result_pos + n) for n in range(len(c_nfd))])
    return result, indices


def normalize_to_NFC_with_indices(
    inp: str, norm_form: str
) -> Tuple[str, List[Tuple[int, int]]]:
    """Normalize to NFC and return the indices mapping input to output characters"""
    assert norm_form in ("NFC", "NFKC")
    inp_nfc = ud.normalize(norm_form, inp)
    NFD_form = norm_form[:-1] + "D"  # NFC->NFD or NFKC->NFKD
    inp_nfd, indices_to_nfd = normalize_to_NFD_with_indices(inp, NFD_form)
    remapped_nfd, reverse_indices_to_nfc = normalize_to_NFD_with_indices(
        inp_nfc, NFD_form
    )
    assert inp_nfd == remapped_nfd
    indices_to_nfc = [(b, a) for a, b in reverse_indices_to_nfc]
    return inp_nfc, compose_indices(indices_to_nfd, indices_to_nfc)


def normalize_with_indices(
    inp: str, norm_form: str
) -> Tuple[str, List[Tuple[int, int]]]:
    """Normalize inp to the specified norm_form (NFC, NFD, NFKC, or NFKD)

    Returns:
        Tuple(normalized string, mapping indices)
    """
    if norm_form in ("NFC", "NFKC"):
        return normalize_to_NFC_with_indices(inp, norm_form)
    if norm_form in ("NFD", "NFKD"):
        return normalize_to_NFD_with_indices(inp, norm_form)
    if norm_form in ("none", None):
        return inp, [(i, i) for i in range(len(inp))]
    raise exceptions.InvalidNormalization(normalize)


def unicode_escape(text):
    """Find any escaped characters and turn them into codepoints"""
    return re.sub(r"""\\(u[0-9A-Fa-f]{4}|U[0-9A-Fa-f]{6})""", escape_to_codepoint, text)


def escape_to_codepoint(match):
    """Turn escape into codepoint"""
    hex_codepoint = match.group(1)[1:]
    return chr(int(hex_codepoint, base=16))


EXPLICIT_INDEX_PATTERN = re.compile(r"{\d+}")


def strip_index_notation(string: str) -> str:
    """Return a string stripped of any explicit indices

    >>> strip_index_notation('test')
    'test'

    >>> strip_index_notation('t{0}e{2}st')
    'test'

    Args:
        string (str): a string that might have explicit indices

    Returns:
        str: a string without explicit indices
    """
    return re.sub(EXPLICIT_INDEX_PATTERN, "", string)


def create_fixed_width_lookbehind(pattern):
    """Turn all characters into fixed width lookbehinds"""
    return re.sub(
        re.compile(
            r"""
    (?<=\(?)              # lookbehind
    [\\\[\]\p{L}\p{M}|.:'^$]+  # match any number of Unicode characters and diacritics, plus square brackets, and backslash so patterns like \b can be used
    (?=\)?)               # lookahead
    """,
            re.U | re.VERBOSE,
        ),
        pattern_to_fixed_width_lookbehinds,
        pattern,
    )


def pattern_to_fixed_width_lookbehinds(match):
    """Python must have fixed-width lookbehinds."""
    pattern = match.group()
    pattern = sorted(pattern.split("|"), key=len, reverse=True)
    # in python ^ and $ have null length so must be ordered differently for proper
    # fixed-width lookbehinds
    null_length_characters = ["^", "$"]
    current_len = 0 if pattern[0] in null_length_characters else len(pattern[0])
    all_lookbehinds = []
    current_list = []
    for item in pattern:
        item_length = 0 if item in null_length_characters else len(item)
        if item_length == current_len:
            current_list.append(item)
        else:
            current_len = item_length
            all_lookbehinds.append(current_list)
            current_list = [item]
        if pattern.index(item) == len(pattern) - 1:
            all_lookbehinds.append(current_list)
    all_lookbehinds = [f"(?<={'|'.join(items)})" for items in all_lookbehinds]
    return "(" + "|".join(all_lookbehinds) + ")"


def load_from_workbook(language):
    """Parse mapping from Excel workbook"""
    from openpyxl import load_workbook  # Expensive import, do it only when needed

    try:
        work_book = load_workbook(language, read_only=True)
        work_sheet = work_book.active
        # Create wordlist
        mapping = []
        # Loop through rows in worksheet, create if statements for different columns
        # and append mappings to self.mapping.
        for row in work_sheet:
            new_io = {"in": "", "out": "", "context_before": "", "context_after": ""}
            for cell in row:
                if cell.value is None:  # avoid tripping on empty cells
                    continue
                if cell.column in ["A", 1]:
                    new_io["in"] = str(cell.value)
                elif cell.column in ["B", 2]:
                    new_io["out"] = str(cell.value)
                elif cell.column in ["C", 3] and cell.value is not None:
                    new_io["context_before"] = str(cell.value)
                elif cell.column in ["D", 4] and cell.value is not None:
                    new_io["context_after"] = str(cell.value)
            mapping.append(new_io)
    finally:
        work_book.close()

    return mapping


def load_from_csv(language, delimiter=","):
    """Parse mapping from csv"""
    work_sheet = []
    with open(language, encoding="utf8") as f:
        reader = csv.reader(f, delimiter=delimiter)
        for line in reader:
            work_sheet.append(line)
    # Create wordlist
    mapping = []
    # Loop through rows in worksheet, remove any stray BOMs
    # (zero-width non-breaking spaces), create if statements for
    # different columns and append mappings to self.mapping.
    remove_bom = str.maketrans("", "", "\ufeff")
    for entry in work_sheet:
        new_io = {"in": "", "out": "", "context_before": "", "context_after": ""}
        if len(entry) == 0:
            # Just ignore empty lines in the CSV file
            continue

        if len(entry) == 1:
            raise exceptions.MalformedMapping(
                'Entry {} in mapping {} has no "out" value.'.format(entry, language)
            )

        new_io["in"] = entry[0].translate(remove_bom)
        new_io["out"] = entry[1].translate(remove_bom)
        try:
            new_io["context_before"] = entry[2].translate(remove_bom)
        except IndexError:
            new_io["context_before"] = ""
        try:
            new_io["context_after"] = entry[3].translate(remove_bom)
        except IndexError:
            new_io["context_after"] = ""
        for k in new_io:
            if isinstance(new_io[k], (float, int)):
                new_io[k] = str(new_io[k])
        mapping.append(new_io)

    return mapping


def load_from_file(path: Union[Path, str]) -> list:
    """Helper method to load mapping from file."""
    path = str(path)
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
    if not mapping:
        raise exceptions.MalformedMapping(
            f"Sorry, the file {path} does not contain any rules."
        )
    return mapping


def find_mapping_type(name):
    """Return the type of a mapping given its name"""
    if is_ipa(name):
        return "IPA"
    elif is_xsampa(name):
        return "XSAMPA"
    elif is_dummy(name):
        return "dummy"
    else:
        return "custom"


def escape_special_characters(to_escape: Union[Rule, Dict[str, str]]) -> Rule:
    if isinstance(to_escape, dict):
        to_escape = Rule(**to_escape)
    for key in ["rule_input", "context_before", "context_after"]:
        escaped = re.escape(getattr(to_escape, key))
        if getattr(to_escape, key) != escaped:
            LOGGER.debug(
                f"Escaped special characters in '{getattr(to_escape, key)}' with '{escaped}'. Set 'escape_special' "
                "to False in your Mapping configuration to disable this."
            )
        setattr(to_escape, key, escaped)
    return to_escape


def load_abbreviations_from_file(path: Union[str, Path]):
    """Helper method to load abbreviations from file."""
    path = str(path)
    if path.endswith("csv"):
        abbs = []
        with open(path, encoding="utf8") as f:
            reader = csv.reader(f, delimiter=",")
            abbs = flatten_abbreviations_format(reader)
    elif path.endswith("tsv"):
        abbs = []
        with open(path, encoding="utf8") as f:
            reader = csv.reader(f, delimiter="\t")
            abbs = flatten_abbreviations_format(reader)
    elif path.endswith("psv"):
        abbs = []
        with open(path, encoding="utf8") as f:
            reader = csv.reader(f, delimiter="|")
            abbs = flatten_abbreviations_format(reader)
    else:
        raise exceptions.IncorrectFileType(
            f"Sorry, abbreviations must be stored as CSV/TSV/PSV files. You provided the following: {path}"
        )
    return abbs


def get_alignment_input_string(alignment: str) -> str:
    """Parse one alignment of the format in *.aligned.txt and return just the input"""
    return "".join(
        [
            tok
            for mapping in alignment.split()
            for tok in mapping[: mapping.rindex("}")].split("|")
            if tok != "_"
        ]
    )


def get_alignment_sequence(alignment: str, delimiter="") -> List[Tuple[int, str]]:
    """Parse one alignment of the format in *.aligned.txt and return just the output seq.

    E.g.: a}ʌ b}b a}æ s|h}ʃ e|d}t (from cmudict.ipa.aligned.txt)
    means "abashed" is pronounced /ʌbæʃt/ with the grapheme-phoneme alignment being
    [(1, "ʌ"), (1, "b"), (1, "æ"), (2, "ʃ"), (2, "t")]

    Returns: the alignment as a List[Tuple[int, str]] where the int is the number
             of input characters consumed and the str are the output phoneme(s).
    """
    mappings: List[Tuple[int, str]] = []
    for mapping in alignment.split():
        idx = mapping.rindex("}")
        # Note that we care about *character* indices, so we join them together
        in_len = sum(len(tok) for tok in mapping[:idx].split("|") if tok != "_")
        out_seq = delimiter.join(
            tok for tok in mapping[idx + 1 :].split("|") if tok != "_"
        )
        # To save space, make the mappings flat and only store
        # the number of input characters rather than the characters themselves
        mappings.append((in_len, out_seq))
    return mappings


# The joiner between key and value must be 0 so that it sorts before all
# characters and thus won't break bisect_left()
_JOINER = "\0"


def find_alignment(alignments: List[str], word: str) -> List[Tuple[int, str]]:
    """Given a sorted list of (word, alignment), find word and return its parsed alignment."""
    i = bisect_left(alignments, word)
    if i != len(alignments):
        k, v = alignments[i].split(_JOINER, maxsplit=1)
        if k == word:
            return get_alignment_sequence(v)
    return []


def load_alignments_from_file(path, delimiter="") -> List[str]:
    """Load alignments in Phonetisaurus default format.

    Returns a mapping of input words to output alignments used to
    create a lexicon mapping.  These are of the form (length,
    outputs, length, outputs, ...) - that is, a sequence of pairs
    specifying how much of the input to consume and what it maps
    to.  This particular format is used to avoid redundancy with
    the keys in the dictionary.
    """
    LOGGER.info("Loading alignments from %s", path)
    alignments = []
    with open(path, encoding="utf8") as f:
        for spam in f:
            spam = spam.strip()
            if not spam:
                continue
            word = get_alignment_input_string(spam)
            alignments.append(word + _JOINER + spam)
    return sorted(alignments)


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

    def ignore_aliases(self, *_args):
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
    """Maps a character to one of [ "letter", "number", "diacritic", "punctuation",
    "symbol", "whitespace", "other"]"""
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
            ordered_rule = {"in": obj["in"], "out": obj["out"], **obj}
            assert obj == ordered_rule
            return json.dumps(ordered_rule, ensure_ascii=self.ensure_ascii)
        elif isinstance(obj, (list, tuple)):
            self.indentation_level += 1
            output = [self.indent_str + self.encode(el) for el in obj]
            self.indentation_level -= 1
            return "[\n" + ",\n".join(output) + "\n" + self.indent_str + "]"
        elif isinstance(obj, dict):
            self.indentation_level += 1
            output = [
                self.indent_str + f"{json.dumps(k)}: {self.encode(v)}"
                for k, v in obj.items()
            ]
            self.indentation_level -= 1
            return "{\n" + ",\n".join(output) + "\n" + self.indent_str + "}"
        else:
            return json.dumps(obj, ensure_ascii=self.ensure_ascii)

    @property
    def indent_str(self) -> str:
        return " " * self.indentation_level * self.indent

    def iterencode(self, obj, **kwargs):
        return self.encode(obj)


class MAPPING_TYPE(str, Enum):
    mapping = "mapping"
    unidecode = "unidecode"
    lexicon = "lexicon"


class NORM_FORM_ENUM(str, Enum):
    NFC = "NFC"
    NFD = "NFD"
    NKFC = "NKFC"
    NKFD = "NKFD"
    none = "none"


class RULE_ORDERING_ENUM(str, Enum):
    as_written = "as-written"
    apply_longest_first = "apply-longest-first"


class _MappingModelDefinition(BaseModel):
    parent_dir: Optional[DirectoryPath] = None
    """Optionally resolve all paths to a parent directory"""

    id: Optional[str] = None
    """A unique ID for the mapping"""

    in_lang: str = "standalone"
    """The input language ID"""

    out_lang: str = "standalone"
    """The output language ID"""

    language_name: Optional[str] = None
    """The name of the language"""

    display_name: Optional[str] = None
    """The display name of the mapping"""

    as_is: Optional[bool] = None
    """Deprecated: Please use rule_ordering='as_written' """

    case_sensitive: bool = True
    """When false, lowercase all rules and conversion input"""

    case_equivalencies: dict = {}
    """List of case equivalencies for preserve_case that are not already in the Unicode standard"""

    preserve_case: bool = False
    """Preserve source case in output (requires case_sensitive=False)"""

    escape_special: bool = False
    """Escape special characters in rules"""

    norm_form: NORM_FORM_ENUM = NORM_FORM_ENUM.NFD
    """Normalization standard to follow"""

    out_delimiter: str = ""
    """Separate output transformations with a delimiter"""

    reverse: bool = False
    """Reverse all mappings."""

    rule_ordering: RULE_ORDERING_ENUM = RULE_ORDERING_ENUM.as_written
    """ Affects in what order the rules are applied.

        If set to ``"as-written"``, rules are applied from top-to-bottom in the order that they
        are written in the source file
        (previously this was accomplished with ``as_is=True``).

        If set to ``"apply-longest-first"``, rules are first sorted such that rules with the longest
        input are applied first. Sorting the rules like this prevents shorter rules
        from taking part in feeding relations
        (previously this was accomplished with ``as_is=False``)
    """

    prevent_feeding: bool = False
    """Converts each rule into an intermediary form in the Unicode PUA"""

    type: Optional[MAPPING_TYPE] = None
    """Type of mapping, either "mapping" (rules), "unidecode" (magical Unicode guessing) or
        "lexicon" (lookup in an aligned lexicon)."""

    alignments: List[str] = []
    """The alignments for a lexicon mapping"""

    alignments_path: Optional[Path] = None
    """A path specifying a file from which to load alignments when type = 'lexicon'"""

    authors: Optional[List[str]] = None
    """A list of authors responsible for the mapping."""

    abbreviations: Dict[str, List[str]] = {}
    """A list of 'abbreviations' for your mappings. Please see https://blog.mothertongues.org/g2p-advanced-mappings/ for more information."""

    abbreviations_path: Optional[Path] = None
    """A path to an 'abbreviations' file"""

    rules: List[Rule] = []
    """A list of Rules"""

    rules_path: Optional[Path] = None
    """A path to a file of a list of rules"""

    model_config = ConfigDict(str_strip_whitespace=False, extra="allow")

    @model_validator(mode="after")
    def check_mapping_types(self) -> "_MappingModelDefinition":
        if (
            (self.type == MAPPING_TYPE.mapping or self.type is None)
            and not self.rules
            and self.rules_path is None
        ):
            LOGGER.warning(
                exceptions.MalformedMapping(
                    "You have to either specify some rules or a path to a file containing rules."
                )
            )
        if (
            (self.type == MAPPING_TYPE.lexicon)
            and not self.alignments
            and self.alignments_path is None
        ):
            raise exceptions.MalformedMapping(
                "Lexicon mappings must also provide alignments"
            )
        return self

    @field_serializer("rules_path", "abbreviations_path", "alignments_path")
    def serialize_paths(self, path: Path):
        return path.name if path else path

    @field_serializer("rules")
    def serialize_mapping(self, rules: List[Rule]):
        return [rule.export_to_dict() for rule in rules]

    @field_validator("norm_form", mode="before")
    @classmethod
    def validate_norm_form(cls, v):
        if not v or v is None:
            v = "none"
        return v

    @field_validator("case_equivalencies", mode="before")
    @classmethod
    def validate_case_equivalencies(cls, v):
        if not v or v is None:
            v = {}
        for lower_case, upper_case in v.items():
            if len(lower_case) != len(upper_case):
                raise exceptions.MalformedMapping(
                    f"Sorry, the case equivalency between {lower_case} and {upper_case} is not valid because it is not the same length, please write rules such that any case equivalent is of equal length."
                )
        return v

    @model_validator(mode="after")
    def validate_preserve_case(self):
        """preserve_case=True requires case_sensitive=False"""
        if self.preserve_case and self.case_sensitive:
            raise exceptions.MalformedMapping(
                "Sorry, preserve_case=True requires case_sensitive=False."
            )
        return self

    @field_validator(
        "rules_path", "abbreviations_path", "alignments_path", mode="before"
    )
    @classmethod
    def add_parent_dir(cls, value: Any, info: ValidationInfo):
        """If there is a parent directory, prepend it to all path fields."""
        if isinstance(value, (str, Path)):
            if info.data.get("parent_dir", None):
                value = Path(info.data["parent_dir"]) / value
        return value

    @model_validator(mode="before")
    @classmethod
    def create_language_name(cls, data: Any):
        """When missing, default language_name to in_lang"""
        if isinstance(data, dict) and data.get("language_name", None) is None:
            data["language_name"] = data.get("in_lang", None)
        return data

    @model_validator(mode="before")
    @classmethod
    def create_display_name(cls, data: Any):
        """When missing, create a default display_name from in_lang and out_lang"""
        if isinstance(data, dict) and data.get("display_name", None) is None:
            in_lang = data.get("in_lang", "")
            out_lang = data.get("out_lang", "")
            data["display_name"] = (
                f"{in_lang} {find_mapping_type(in_lang)} to "
                f"{out_lang} {find_mapping_type(out_lang)}"
            )
        return data
