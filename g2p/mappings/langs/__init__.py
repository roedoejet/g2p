"""
Language mappings for g2p.
"""
import os
import pickle

from networkx import read_gpickle
from g2p.exceptions import MalformedMapping

LANGS_DIR = os.path.dirname(__file__)
LANGS_PKL_NAME = "langs.pkl"
LANGS_PKL = os.path.join(LANGS_DIR, LANGS_PKL_NAME)
NETWORK_PKL_NAME = "network.pkl"
LANGS_NWORK_PATH = os.path.join(LANGS_DIR, NETWORK_PKL_NAME)

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
LANGS_AVAILABLE = sorted(language_names)
MAPPINGS_AVAILABLE = []
for k, v in LANGS.items():
    if "mappings" in v:
        MAPPINGS_AVAILABLE.extend(v["mappings"])
    else:
        MAPPINGS_AVAILABLE.append(v)
