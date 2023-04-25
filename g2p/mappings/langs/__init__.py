"""
Language mappings for g2p.
"""
import os
import pickle

from networkx import DiGraph, read_gpickle

from g2p.log import LOGGER

LANGS_DIR = os.path.dirname(__file__)
LANGS_PKL_NAME = "langs.pkl"
LANGS_PKL = os.path.join(LANGS_DIR, LANGS_PKL_NAME)
NETWORK_PKL_NAME = "network.pkl"
LANGS_NWORK_PATH = os.path.join(LANGS_DIR, NETWORK_PKL_NAME)


def load_langs(path: str = LANGS_PKL):
    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        LOGGER.warning(f"Failed to read language cache from {path}: {e}")
        return {}


def load_network(path: str = LANGS_NWORK_PATH):
    try:
        return read_gpickle(path)
    except Exception as e:
        LOGGER.warning(f"Failed to read language network from {path}: {e}")
        return DiGraph()


def get_available_languages(langs: dict) -> list:
    language_names = set()
    for k, v in langs.items():
        if k in ["generated", "font-encodings"]:
            continue
        if "mappings" in v:
            for vv in v["mappings"]:
                if "language_name" in vv:
                    language_names.add(vv["language_name"])
        elif "language_name" in v:
            language_names.add(v["language_name"])
    return sorted(language_names)


def get_available_mappings(langs: dict) -> list:
    mappings_available = []
    for k, v in langs.items():
        if "mappings" in v:
            mappings_available.extend(v["mappings"])
        else:
            mappings_available.append(v)
    return mappings_available


LANGS = load_langs()
LANGS_NETWORK = load_network()
LANGS_AVAILABLE = get_available_languages(LANGS)
MAPPINGS_AVAILABLE = get_available_mappings(LANGS)


def reload_db():
    """Reload the langs and network data, necessary after a g2p update."""

    # We update all structures in place, so that another module having done from
    # g2p.mappings.langs import VAR will see the udpates without any code changes.

    global LANGS
    LANGS.clear()
    LANGS.update(load_langs())

    global LANGS_NETWORK
    LANGS_NETWORK.clear()
    new_langs_network = load_network()
    LANGS_NETWORK.update(new_langs_network.edges, new_langs_network.nodes)

    global LANGS_AVAILABLE
    LANGS_AVAILABLE.clear()
    LANGS_AVAILABLE.extend(get_available_languages(LANGS))

    global MAPPINGS_AVAILABLE
    MAPPINGS_AVAILABLE.clear()
    MAPPINGS_AVAILABLE.extend(get_available_mappings(LANGS))
