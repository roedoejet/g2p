"""

Utilities used by other classes

"""

import panphon.distance
from g2p.log import LOGGER
from g2p.mappings import Mapping
from g2p.mappings.langs import MAPPINGS_AVAILABLE


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
        _PANPHON_DISTANCE_SINGLETON = panphon.distance.Distance()
    return _PANPHON_DISTANCE_SINGLETON


def check_ipa_known_segs(mappings_to_check=False):
    dst = getPanphonDistanceSingleton()
    if not mappings_to_check:
        mappings_to_check = [x["out_lang"] for x in MAPPINGS_AVAILABLE]
    found_error = False
    for mapping in [
        x for x in MAPPINGS_AVAILABLE if x["out_lang"] in mappings_to_check
    ]:
        if mapping["out_lang"].endswith("-ipa"):
            for rule in mapping["mapping_data"]:
                joined_ipa_segs = "".join(dst.fm.ipa_segs(rule["out"]))
                if not joined_ipa_segs == rule["out"]:
                    LOGGER.warning(
                        f"Output '{rule['out']}' in rule {rule} in mapping between {mapping['in_lang']} and {mapping['out_lang']} is not recognized as valid IPA by panphon. You may ignore this warning if you know it gets remapped to IPA later."
                    )
                    found_error = True
    if found_error:
        LOGGER.warning(
            "Please refer to https://github.com/dmort27/panphon for information about panphon."
        )


def is_panphon(string):
    dst = getPanphonDistanceSingleton()
    for word in string.split():
        if not word == "".join(dst.fm.ipa_segs(word)):
            return False
    return True


_ARPABET_SET = set(Mapping(in_lang="eng-ipa", out_lang="eng-arpabet").inventory("out"))


def is_arpabet(string):
    # print(f"arpabet_set={_ARPABET_SET}")
    for sound in string.split():
        if sound not in _ARPABET_SET:
            return False
    return True
