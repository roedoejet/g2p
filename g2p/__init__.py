"""

Basic init file for g2p module

"""
import sys
import io

from networkx import shortest_path
from networkx.exception import NetworkXNoPath

from g2p.exceptions import InvalidLanguageCode, NoPath
from g2p.mappings import Mapping
from g2p.mappings.langs import LANGS_NETWORK
import g2p.mappings.tokenizer as tok
from g2p.transducer import CompositeTransducer, Transducer, TokenizingTransducer
from g2p.log import LOGGER

if sys.stdout.encoding != 'utf8' and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf8")

if sys.stderr.encoding != 'utf8' and hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf8")


_g2p_cache = {}

def make_g2p(in_lang: str, out_lang: str, tok_lang=None):
    """Make a g2p Transducer for mapping text from in_lang to out_lang via the
    shortest path between them.

    Args:
        in_lang (str): input language code
        out_lang (str): output language code

    Returns:
        Transducer from in_lang to out_lang

    Raises:
        InvalidLanguageCode: if in_lang or out_lang don't exist
        NoPath: if there is path between in_lang and out_lang
    """
    if (in_lang, out_lang, tok_lang) in _g2p_cache:
        return _g2p_cache[(in_lang, out_lang, tok_lang)]

    # Check in_lang is a node in network
    if in_lang not in LANGS_NETWORK.nodes:
        LOGGER.error(f"No lang called '{in_lang}'. Please try again.")
        raise InvalidLanguageCode(in_lang)

    # Check out_lang is a node in network
    if out_lang not in LANGS_NETWORK.nodes:
        LOGGER.error(f"No lang called '{out_lang}'. Please try again.")
        raise InvalidLanguageCode(out_lang)

    # Try to find the shortest path between the nodes
    try:
        path = shortest_path(LANGS_NETWORK, in_lang, out_lang)
    except NetworkXNoPath as e:
        LOGGER.error(f"Sorry, we couldn't find a way to convert {in_lang} to {out_lang}. Please update your langs by running `g2p update` and try again.")
        raise NoPath(in_lang, out_lang) from e

    # Find all mappings needed
    mappings_needed = []
    for lang1, lang2 in zip(path[:-1], path[1:]):
        mapping = Mapping(in_lang=lang1, out_lang=lang2)
        LOGGER.debug(f"Adding mapping between {lang1} and {lang2} to composite transducer.")
        mappings_needed.append(mapping)

    # Either construct a Transducer or Composite Transducer
    if len(mappings_needed) == 1:
        transducer = Transducer(mappings_needed[0])
    else:
        transducer = CompositeTransducer([Transducer(x) for x in mappings_needed])

    # If tokenization was requested, return a TokenizingTransducer
    if tok_lang:
        if tok_lang == "path":
            tokenizer = tok.get_tokenizer(in_lang=in_lang, tok_path=path)
        else:
            tokenizer = tok.get_tokenizer(in_lang=tok_lang)
        transducer = TokenizingTransducer(transducer, tokenizer)

    _g2p_cache[(in_lang, out_lang, tok_lang)] = transducer
    return transducer


def get_tokenizer(in_lang=None):
    return tok.get_tokenizer(in_lang)


def tokenize_and_map(tokenizer, transducer, input: str):
    result = ""
    for token in tokenizer.tokenize_text(input):
        if token["is_word"]:
            result += transducer(token["text"]).output_string
        else:
            result += token["text"]
    return result
