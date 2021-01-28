"""

Tokenizer module, to provide language-dependent tokenization of text.
A token is defined as a sequence of characters that are either part of the
language's input mapping or that are unicode letters, numbers and diacritics.

"""
import re
from g2p.mappings import Mapping
from g2p.mappings.utils import merge_if_same_label, get_unicode_category
from g2p.exceptions import MappingMissing

class DefaultTokenizer:
    def __init__(self):
        self.inventory = []
        self.delim = ""
        self.case_sensitive = False

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
        units = merge_if_same_label(units, "text", "is_word")
        return units


class Tokenizer(DefaultTokenizer):
    def __init__(self, mapping: Mapping):
        self.inventory = mapping.inventory("in")
        self.lang = mapping.kwargs.get("language_name", "")
        self.delim = mapping.kwargs.get("in_delimiter", "")
        self.case_sensitive = mapping.kwargs.get("case_sensitive", True)
        # create regex

        regex_pieces = sorted(self.inventory, key=lambda s: -len(s))
        regex_pieces = [re.escape(p) for p in regex_pieces]
        if self.delim:
            regex_pieces.append(self.delim)
        pattern = "|".join(regex_pieces + ["."])
        pattern = "(" + pattern + ")"
        flags = re.DOTALL
        if not self.case_sensitive:
            flags |= re.I
        self.regex = re.compile(pattern, flags)

    def tokenize_aux(self, text):
        return self.regex.findall(text)


class TokenizerLibrary:
    """
    The TokenizerLibrary holds the collection of tokenizers that have been
    initialized so far. We don't initialize them all since that takes costly
    loading time; instead, we initialize each only as requested.
    """

    def __init__(self):
        self.tokenizers = {None: DefaultTokenizer()}

    def get_tokenizer_key(self, in_lang, out_lang=None):
        if not in_lang:
            return None
        if not out_lang:
            out_lang = in_lang + "-ipa"
        return in_lang + "-to-" + out_lang

    def get_tokenizer(self, in_lang, out_lang=None):
        tokenizer_key = self.get_tokenizer_key(in_lang, out_lang)
        if not self.tokenizers.get(tokenizer_key):
            # This tokenizer was not created yet, initialize it now.
            if not out_lang:
                out_lang = in_lang + "-ipa"
            try:
                mapping = Mapping(in_lang=in_lang, out_lang=out_lang)
                self.tokenizers[tokenizer_key] = Tokenizer(mapping)
            except MappingMissing:
                self.tokenizers[tokenizer_key] = self.tokenizers[None]

        return self.tokenizers.get(tokenizer_key)


_TOKENIZER_LIBRARY = TokenizerLibrary()

def get_tokenizer(in_lang=None):
    return _TOKENIZER_LIBRARY.get_tokenizer(in_lang)
