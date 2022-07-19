"""

Utilities used by other classes

"""

import pickle
from pathlib import Path

import yaml
from networkx import DiGraph, write_gpickle

from g2p.exceptions import MalformedMapping
from g2p.log import LOGGER
from g2p.mappings import Mapping
from g2p.mappings.langs import (
    LANGS_DIR,
    LANGS_NWORK_PATH,
    LANGS_PKL,
    MAPPINGS_AVAILABLE,
)
from g2p.mappings.utils import is_ipa, load_mapping_from_path

# panphon.distance.Distance() takes a long time to initialize, so...
# a) we don't want to load it if we don't need it, i.e., don't use a constant
# b) we don't want to load it more than once, i.e., don't use a local variable.
# Conclusion: use a singleton with lazy initialization
# Profiling results: calling is_panphon() the first time still costs 400ms, but subsequent
# calls cost .02ms each. With dst=panphone.distance.Distance() instead of
# dst=getPanphonDistanceSingleton(), the first call costs 400ms and subsequent calls
# cost 180ms each.

_PANPHON_DISTANCE_SINGLETON = None


def getPanphonDistanceSingleton():
    global _PANPHON_DISTANCE_SINGLETON
    if _PANPHON_DISTANCE_SINGLETON is None:
        import panphon.distance  # Expensive import, only do it when actually needed

        _PANPHON_DISTANCE_SINGLETON = panphon.distance.Distance()
    return _PANPHON_DISTANCE_SINGLETON


def check_ipa_known_segs(mappings_to_check=False) -> bool:
    """Check the given mappings, or all IPA mappings, for invalid IPA in the "out" fields

    Returns True iff not errors were found.
    """
    if not mappings_to_check:
        mappings_to_check = [x["out_lang"] for x in MAPPINGS_AVAILABLE]
    found_error = False
    for mapping in [
        x for x in MAPPINGS_AVAILABLE if x["out_lang"] in mappings_to_check
    ]:
        if is_ipa(mapping["out_lang"]):
            reverse = mapping.get("reverse", False)
            for rule in mapping["mapping_data"]:
                output = rule["in"] if reverse else rule["out"]
                if not is_panphon(output):
                    LOGGER.warning(
                        f"Output '{rule['out']}' in rule {rule} in mapping between {mapping['in_lang']} "
                        f"and {mapping['out_lang']} is not recognized as valid IPA by panphon."
                    )
                    found_error = True
    if found_error:
        LOGGER.warning(
            "Please refer to https://github.com/dmort27/panphon for information about panphon."
        )
    return not found_error


_is_panphon_g_warning_printed = False
_is_panphon_colon_warning_printed = False


def is_panphon(string, display_warnings=False):
    # Deferred importing required here, because g2p.transducer also imports this file.
    # Such circular dependency is probably bad design, maybe a reviewer of this code will
    # have a better solution to recommend?
    import g2p.transducer

    dst = getPanphonDistanceSingleton()
    panphon_preprocessor = g2p.transducer.Transducer(Mapping(id="panphon_preprocessor"))
    preprocessed_string = panphon_preprocessor(string).output_string
    # Use a loop that prints the warnings on all strings that are not panphon, even though
    # logically this should not be necessary to calculate the answer.
    result = True
    for word in preprocessed_string.split():
        word_ipa_segs = dst.fm.ipa_segs(word)
        word_ipa = "".join(word_ipa_segs)
        if word != word_ipa:
            if not display_warnings:
                return False
            LOGGER.warning(
                f'String "{word}" is not identical to its IPA segmentation: {word_ipa_segs}'
            )
            global _is_panphon_g_warning_printed
            if "g" in word and not _is_panphon_g_warning_printed:
                LOGGER.warning(
                    "Common IPA gotcha: the ASCII 'g' character is not IPA, use 'ɡ' (\\u0261) instead."
                )
                _is_panphon_g_warning_printed = True
            global _is_panphon_colon_warning_printed
            if ":" in word and not _is_panphon_colon_warning_printed:
                LOGGER.warning(
                    "Common IPA gotcha: the ASCII ':' character is not IPA, use 'ː' (\\u02D0) instead."
                )
                _is_panphon_colon_warning_printed = True
            for c in word:
                if c not in word_ipa:
                    LOGGER.warning(
                        f"Character '{c}' (\\u{format(ord(c), '04x')}) in word '{word}' "
                        "was not recognized as IPA by panphon."
                    )
            result = False
    return result


_ARPABET_SET = None


def is_arpabet(string):
    global _ARPABET_SET
    if _ARPABET_SET is None:
        _ARPABET_SET = set(
            Mapping(in_lang="eng-ipa", out_lang="eng-arpabet").inventory("out")
        )
    # print(f"arpabet_set={_ARPABET_SET}")
    for sound in string.split():
        if sound not in _ARPABET_SET:
            return False
    return True


def cache_langs(
    dir_path: str = LANGS_DIR,
    langs_path: str = LANGS_PKL,
    network_path: str = LANGS_NWORK_PATH,
):
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

    # Sort by language code
    paths = sorted(Path(dir_path).glob("./*/config.y*ml"), key=lambda x: x.parent.stem)
    mappings_legal_pairs = []
    for path in paths:
        code = path.parent.stem
        with open(path, encoding="utf8") as f:
            data = yaml.safe_load(f)
        # If there is a mappings key, there is more than one mapping
        # TODO: should put in some measure to prioritize non-generated
        # mappings and warn when they override
        if "mappings" in data:
            for index, mapping in enumerate(data["mappings"]):
                in_lang = data["mappings"][index]["in_lang"]
                out_lang = data["mappings"][index]["out_lang"]
                mappings_legal_pairs.append((in_lang, out_lang))
                if "language_name" not in mapping:
                    raise MalformedMapping(
                        f"language_name missing in {path} from mapping "
                        f"from {in_lang} to {out_lang}"
                    )
                data["mappings"][index] = load_mapping_from_path(path, index)
        else:
            data = load_mapping_from_path(path)
            if "language_name" not in data:
                raise MalformedMapping(f"language_name missing in {path}")
        langs[code] = data

    # Save as a Directional Graph
    lang_network = DiGraph()
    lang_network.add_edges_from(mappings_legal_pairs)

    with open(network_path, "wb") as f:
        write_gpickle(lang_network, f, protocol=4)

    with open(langs_path, "wb") as f:
        pickle.dump(langs, f, protocol=4)

    return langs
