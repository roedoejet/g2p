"""

Utilities used by other classes

"""

from panphon import distance

from g2p.log import LOGGER
from g2p.mappings.langs import MAPPINGS_AVAILABLE

def check_ipa_known_segs(mappings_to_check=False):
    dst = distance.Distance()
    if not mappings_to_check:
        mappings_to_check = MAPPINGS_AVAILABLE
    for mapping in [x for x in MAPPINGS_AVAILABLE if x['out_lang'] in mappings_to_check]:
        if mapping['out_lang'].endswith('-ipa'):
            for rule in mapping['mapping_data']:
                joined_ipa_segs = ''.join(dst.fm.ipa_segs(rule['out']))
                if not joined_ipa_segs == rule['out']:
                    LOGGER.warn(f"Character '{rule['out']}' in mapping between {mapping['in_lang']} and {mapping['out_lang']} is not recognized as valid IPA by panphon. Please refer to https://github.com/dmort27/panphon")