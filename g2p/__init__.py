"""

Basic init file for g2p module

"""
import sys
import io

from networkx import shortest_path
from networkx.exception import NetworkXNoPath

from g2p.mappings import Mapping
from g2p.mappings.langs import LANGS_NETWORK
from g2p.transducer import CompositeTransducer, Transducer
from g2p.log import LOGGER

if sys.stdout.encoding != 'utf8' and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf8")

if sys.stderr.encoding != 'utf8' and hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf8")

def make_g2p(in_lang: str, out_lang: str):
    # Check in_lang is a node in network
    if in_lang not in LANGS_NETWORK.nodes:
        LOGGER.error(f"No lang called {in_lang}. Please try again.")
        raise(FileNotFoundError("No lang called {in_lang}."))

    # Check out_lang is a node in network
    if out_lang not in LANGS_NETWORK.nodes:
        LOGGER.error(f"No lang called {out_lang}. Please try again.")
        raise(FileNotFoundError("No lang called {out_lang}."))

    # Try to find the shortest path between the nodes
    try:
        path = shortest_path(LANGS_NETWORK, in_lang, out_lang)
    except NetworkXNoPath:
        LOGGER.error(f"Sorry, we couldn't find a way to convert {in_lang} to {out_lang}. Please update your langs by running `g2p update` and try again.")
        raise(NetworkXNoPath)

    # Find all mappings needed
    mappings_needed = []
    for i, lang in enumerate(path):
        try:
            mapping = Mapping(in_lang=path[i], out_lang=path[i+1])
            LOGGER.debug(f"Adding mapping between {path[i]} and {path[i+1]} to composite transducer.")
            mappings_needed.append(mapping)
        except IndexError:
            continue

    # Either return Transducer or Composite Transducer
    if len(mappings_needed) == 1:
        return Transducer(mappings_needed[0])
    else:
        return CompositeTransducer([Transducer(x) for x in mappings_needed])

    
