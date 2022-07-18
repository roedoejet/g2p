"""
Language mappings for g2p.
"""
import os
import pickle

from networkx import read_gpickle, DiGraph
from g2p.exceptions import MalformedMapping
from g2p.log import LOGGER

LANGS_DIR = os.path.dirname(__file__)
LANGS_PKL_NAME = "langs.pkl"
LANGS_PKL = os.path.join(LANGS_DIR, LANGS_PKL_NAME)
NETWORK_PKL_NAME = "network.pkl"
LANGS_NWORK_PATH = os.path.join(LANGS_DIR, NETWORK_PKL_NAME)

# Cache mappings as pickle file for quick loading
try:
    with open(LANGS_PKL, "rb") as f:
        LANGS = pickle.load(f)
except Exception as e:
    LOGGER.warning(
        f"Failed to read language cache from {LANGS_PKL}: {e}")
    LANGS = {}

try:
    LANGS_NETWORK = read_gpickle(LANGS_NWORK_PATH)
except Exception as e:
    LOGGER.warning(
        f"Failed to read language network from {LANGS_NWORK_PATH}: {e}")
    LANGS_NETWORK = DiGraph()

# language_name is not unique for each mapping
language_names = set()
for k, v in LANGS.items():
    if k in ["generated", "font-encodings"]:
        continue
    if "mappings" in v:
        for vv in v["mappings"]:
            if "language_name" in vv:
                language_names.add(vv["language_name"])
    elif "language_name" in v:
        language_names.add(v["language_name"])
LANGS_AVAILABLE = sorted(language_names)
MAPPINGS_AVAILABLE = []
for k, v in LANGS.items():
    if "mappings" in v:
        MAPPINGS_AVAILABLE.extend(v["mappings"])
    else:
        MAPPINGS_AVAILABLE.append(v)
