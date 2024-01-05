"""
This file is for constants that can be initialized without any (expensive) dependencies.
"""

import os

DISTANCE_METRICS = [
    "weighted_feature_edit_distance",
    "hamming_feature_edit_distance",
    "feature_edit_distance",
    "dolgo_prime_distance",
    "fast_levenshtein_distance",
    "levenshtein_distance",
]

LANGS_DIR = os.path.join(os.path.dirname(__file__), "mappings", "langs")
LANGS_FILE_NAME = "langs.json.gz"
NETWORK_FILE_NAME = "network.json.gz"
