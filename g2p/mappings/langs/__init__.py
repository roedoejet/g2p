"""
Language mappings for g2p.
"""
import os
import pickle
import timeit
from copy import deepcopy
from pathlib import Path

import yaml
import argparse
from networkx import DiGraph, read_gpickle, shortest_path, write_gpickle

from g2p.exceptions import MappingMissing, MalformedMapping
from g2p.mappings.utils import find_mapping, load_mapping_from_path

LANGS_DIR = os.path.dirname(__file__)
LANGS_PKL_NAME = "langs.pkl"
LANGS_PKL = os.path.join(LANGS_DIR, LANGS_PKL_NAME)
NETWORK_PKL_NAME = "network.pkl"
LANGS_NWORK_PATH = os.path.join(LANGS_DIR, NETWORK_PKL_NAME)


def cache_langs(dir_path: str = LANGS_DIR,
                langs_path: str = LANGS_PKL,
                network_path: str = LANGS_NWORK_PATH):
    """Read in all files and save as pickle.

    Args:
       dir_path: Path to scan for config.yaml files.  Default is the
                 installed g2p/mappings/langs directory.
       langs_path: Path to output langs.pkl pickle file.  Default is
                   the installed g2p/mappings/langs/langs.pkl
       network_path: Path to output pickle file.  Default is the
                     installed g2p/mappings/langs/network.pkl.
    """
    langs = {}
    dir_path = Path(dir_path)
        
    # Sort by language code
    paths = sorted(dir_path.glob("./*/config.y*ml"), key=lambda x: x.parent.stem)
    mappings_legal_pairs = []
    for path in paths:
        code = path.parent.stem
        with open(path, encoding="utf8") as f:
            data = yaml.safe_load(f)
        # If there is a mappings key, there is more than one mapping
        # TODO: should put in some measure to prioritize non-generated mappings and warn when they override
        if "mappings" in data:
            for index, mapping in enumerate(data["mappings"]):
                mappings_legal_pairs.append(
                    (
                        data["mappings"][index]["in_lang"],
                        data["mappings"][index]["out_lang"],
                    )
                )
                data["mappings"][index] = load_mapping_from_path(path, index)
        else:
            data = load_mapping_from_path(path)
        langs[code] = data

    # Save as a Directional Graph
    lang_network = DiGraph()
    lang_network.add_edges_from(mappings_legal_pairs)

    with open(network_path, "wb") as f:
        write_gpickle(lang_network, f, protocol=4)

    with open(langs_path, "wb") as f:
        pickle.dump(langs, f, protocol=4)

    return langs

LANGS = {}
LANGS_NETWORK = DiGraph()
LANGS_AVAILABLE = []
MAPPINGS_AVAILABLE = []
def load_langs(langs_path: str = LANGS_PKL):
    global LANGS, LANGS_NETWORK, LANGS_AVAILABLE, MAPPINGS_AVAILABLE
    # Cache mappings as pickle file for quick loading
    with open(LANGS_PKL, "rb") as f:
        LANGS = pickle.load(f)

    LANGS_NETWORK = read_gpickle(LANGS_NWORK_PATH)
    for k, v in LANGS.items():
        if k in ["generated", "font-encodings"]:
            continue
        if "mappings" in v:
            for vv in v["mappings"]:
                if "language_name" not in vv:
                    raise MalformedMapping(
                        "language_name missing from mapping for " + k)
    # language_name is not unique for each mapping
    language_names = set()
    for k, v in LANGS.items():
        if k in ["generated", "font-encodings"]:
            continue
        if "mappings" in v:
            for vv in v["mappings"]:
                language_names.add(vv["language_name"])
        else:
            language_names.add(v["language_name"])
    LANGS_AVAILABLE[:] = sorted(language_names)
    del MAPPINGS_AVAILABLE[:]
    for k, v in LANGS.items():
        if "mappings" in v:
            MAPPINGS_AVAILABLE.extend(v["mappings"])
        else:
            MAPPINGS_AVAILABLE.append(v)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-d", "--langdir",
                        default=LANGS_DIR,
                        help="Input directory to scan for language mappings.")
    parser.add_argument("-o", "--outdir",
                        default=LANGS_DIR,
                        help="Ouptut diretory to write cache files.")
    args = parser.parse_args()
    cache_langs(dir_path=args.langdir,
                langs_path=os.path.join(args.outdir, LANGS_PKL_NAME),
                network_path=os.path.join(args.outdir, NETWORK_PKL_NAME))
else:
    load_langs()
