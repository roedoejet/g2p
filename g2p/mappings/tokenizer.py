"""

Tokenizer module, to provide language-dependent tokenization of text.
A token is defined as a sequence of characters that are either part of the
language's input mapping or that are unicode letters, numbers and diacritics.

"""
import re
from g2p.mappings import Mapping
from g2p.mappings.utils import merge_if_same_label, get_unicode_category, is_ipa
from g2p.exceptions import MappingMissing
from g2p.mappings.langs import LANGS_NETWORK
from g2p.log import LOGGER
from networkx.exception import NetworkXError
import pprint


class DefaultTokenizer:
    def __init__(self):
        self.inventory = []
        self.delim = ""
        self.case_sensitive = False
        self.dot_is_letter = False # Hack for Tlingit where . is a letter when not word final

    def tokenize_aux(self, text):
        return text

    def is_word_character(self, c):
        if not self.case_sensitive:
            c = c.lower()
        if c in self.inventory:
            return True
        if self.delim and c == self.delim:
            return True
        assert len(c) <= 1
        if get_unicode_category(c) in ["letter", "number", "diacritic"]:
            return True
        return False

    def tokenize_text(self, text):
        matches = self.tokenize_aux(text)
        units = [{"text": m, "is_word": self.is_word_character(m)} for m in matches]
        if self.dot_is_letter:
            for i, unit in enumerate(units):
                if unit["text"] == "." and i+1 < len(units) and units[i+1]["is_word"]:
                    unit["is_word"] = True
        units = merge_if_same_label(units, "text", "is_word")
        return units


class Tokenizer(DefaultTokenizer):
    def __init__(self, mapping: Mapping):
        self.inventory = mapping.inventory("in")
        self.lang = mapping.kwargs.get("language_name", "")
        self.delim = mapping.kwargs.get("in_delimiter", "")
        self.case_sensitive = mapping.kwargs.get("case_sensitive", True)
        self.dot_is_letter = False
        # create regex
        self._build_regex()

    def _build_regex(self):
        if not self.case_sensitive:
            self.inventory = [c.lower() for c in self.inventory]
        self.inventory = [re.sub(r"{[0-9]+}", "", x) for x in self.inventory]
        regex_pieces = sorted(self.inventory, key=lambda s: -len(s))
        regex_pieces = [re.escape(p) for p in regex_pieces]
        if self.delim:
            regex_pieces.append(self.delim)
        pattern = "|".join(regex_pieces + ["."])
        pattern = "(" + pattern + ")"
        #LOGGER.warning(f"pattern for {self.lang}: {pattern}.")
        flags = re.DOTALL
        if not self.case_sensitive:
            flags |= re.I
        self.regex = re.compile(pattern, flags)

    def tokenize_aux(self, text):
        return self.regex.findall(text)


class MultiHopTokenizer(Tokenizer):
    def __init__(self, mappings: list):
        assert mappings
        self.inventory = sum([m.inventory("in") for m in mappings], [])
        self.lang = mappings[0].kwargs.get("language_name", "")
        self.delim = mappings[0].kwargs.get("in_delimiter", "")
        self.case_sensitive = mappings[0].kwargs.get("case_sensitive", True)
        self.dot_is_letter = False
        self._build_regex()
        # LOGGER.warning(pprint.pformat([self.lang, self.delim, self.case_sensitive, self.inventory]))


class TokenizerLibrary:
    """
    The TokenizerLibrary holds the collection of tokenizers that have been
    initialized so far. We don't initialize them all since that takes costly
    loading time; instead, we initialize each only as requested.
    """

    def __init__(self):
        self.tokenizers = {None: DefaultTokenizer()}

    def get_tokenizer_key(self, in_lang, out_lang=None, tok_path=None):
        if not in_lang:
            return None
        if tok_path:
            return "-to-".join(tok_path)
        if not out_lang:
            out_lang = in_lang + "-ipa"
        return in_lang + "-to-" + out_lang

    def get_tokenizer(self, in_lang, out_lang=None, tok_path=None):
        tokenizer_key = self.get_tokenizer_key(in_lang, out_lang, tok_path)
        if not self.tokenizers.get(tokenizer_key):
            # This tokenizer was not created yet, initialize it now.
            if tok_path:
                #LOGGER.warning(f"in_lang={in_lang} tok_path={tok_path}")
                if tok_path[0] != in_lang:
                    raise ValueError("calling get_tokenizer() with tok_path requires that tok_path[0] == in_lang")
                assert len(tok_path) >= 2
                if len(tok_path) == 2 or is_ipa(tok_path[1]):
                    out_lang = tok_path[1]
                elif len(tok_path) == 3 or is_ipa(tok_path[2]):
                    out_lang = tok_path[1:3]
                elif len(tok_path) > 3 and is_ipa(tok_path[3]):
                    out_lang = tok_path[1:4]
                else:
                    out_lang = tok_path[1:3]
            if not out_lang:
                try:
                    successors = [x for x in LANGS_NETWORK.successors(in_lang)]
                except NetworkXError:
                    successors = []
                ipa_successors = [x for x in successors if is_ipa(x)]
                # LOGGER.warning(pprint.pformat([in_lang, "->", successors, ipa_successors]))
                if ipa_successors:
                    # in_lang has an ipa successor, tokenize using it
                    # there currently are no langs with more than 1 IPA successor, but to
                    # be future-proof we'll arbitrarily take the first if there are more.
                    out_lang = ipa_successors[0]
                else:
                    # There is no direct IPA successor, look for a two-hop path to -ipa
                    for x in successors:
                        ipa_successors_two_hops = [
                            y for y in LANGS_NETWORK.successors(x) if is_ipa(y)
                        ]
                        # LOGGER.warning(pprint.pformat([in_lang, x, "->", [ipa_successors_two_hops]]))
                        if ipa_successors_two_hops:
                            out_lang = [x, ipa_successors_two_hops[0]]
                        break
                    # There is no two-hop IPA successor, use the first direct successor
                    if out_lang is None and successors:
                        out_lang = successors[0]
            #LOGGER.warning(f"Tokenizer for {in_lang} is {out_lang}.")
            if out_lang is None:
                # Default tokenizer:
                self.tokenizers[tokenizer_key] = self.tokenizers[None]
            elif isinstance(out_lang, list):
                # Build a multi-hop tokenizer
                assert len(out_lang) > 1
                try:
                    mappings = [Mapping(in_lang=in_lang, out_lang=out_lang[0])]
                    for i in range(1, len(out_lang)):
                        mappings.append(Mapping(in_lang=out_lang[i - 1], out_lang=out_lang[i]))
                    self.tokenizers[tokenizer_key] = MultiHopTokenizer(mappings)
                except MappingMissing:
                    self.tokenizers[tokenizer_key] = self.tokenizers[None]
                    LOGGER.warning(
                        f"missing mapping yet we looked for mappings in graph for {in_lang}-{out_lang}."
                    )
            else:
                # Build a one-hop tokenizer
                try:
                    mapping = Mapping(in_lang=in_lang, out_lang=out_lang)
                    self.tokenizers[tokenizer_key] = Tokenizer(mapping)
                except MappingMissing:
                    self.tokenizers[tokenizer_key] = self.tokenizers[None]
                    LOGGER.warning(
                        f"Cannot find mapping from '{in_lang}' to '{out_lang}'. Using default tokenizer instead"
                    )

            # Hack for Tlingit using dot as a letter when non word-final
            if in_lang == "tli":
                self.tokenizers[tokenizer_key].dot_is_letter = True

        return self.tokenizers.get(tokenizer_key)


_TOKENIZER_LIBRARY = TokenizerLibrary()


def get_tokenizer(in_lang=None, out_lang=None, tok_path=None):
    """ Get the tokenizer for input in language in_lang

        Logic used when only in_lang is provided:
        - if in_lang -> in_lang-ipa, or in_lang -> X-ipa exists, tokenize using the input
          inventory of that mapping.
        - elif in_lang -> X -> Y-ipa exists, e.g., tce -> tce-equiv -> tce-ipa, tokenize
          using the input inventory of those two hops.
        - otherwise, just use the default tokenizer, which accepts as part of words all
          unicode letter, numbers and diacritics

        Logic used when in_lang and out_lang are provided:
        - if in_lang -> out_lang exists, tokenize using the input inventory of that mapping
        - otherwise use the default tokenizer

        Logic used when in_lang and tok_path are provided:
        - use the first one or two hops in path, stopping at the first -ipa node
    """
    return _TOKENIZER_LIBRARY.get_tokenizer(in_lang, out_lang, tok_path)
