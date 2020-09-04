"""

Utilities used by other classes

"""

from panphon import distance

from g2p.log import LOGGER
from g2p.mappings.langs import MAPPINGS_AVAILABLE

def check_ipa_known_segs(mappings_to_check=False):
    dst = distance.Distance()
    if not mappings_to_check:
        mappings_to_check = [x['out_lang'] for x in MAPPINGS_AVAILABLE]
    found_error = False
    for mapping in [x for x in MAPPINGS_AVAILABLE if x['out_lang'] in mappings_to_check]:
        if mapping['out_lang'].endswith('-ipa'):
            for rule in mapping['mapping_data']:
                joined_ipa_segs = ''.join(dst.fm.ipa_segs(rule['out']))
                if not joined_ipa_segs == rule['out']:
                    LOGGER.warning(f"Output '{rule['out']}' in rule {rule} in mapping between {mapping['in_lang']} and {mapping['out_lang']} is not recognized as valid IPA by panphon. You may ignore this warning if you know it gets remapped to IPA later.")
                    found_error = True
    if found_error:
        LOGGER.warning("Please refer to https://github.com/dmort27/panphon for information about panphon.")
