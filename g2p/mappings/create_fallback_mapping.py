from unidecode import unidecode

from g2p import make_g2p
from g2p.log import LOGGER
from g2p.mappings import Mapping
from g2p.mappings.create_ipa_mapping import align_inventories
from g2p.mappings.utils import generate_config, is_ipa, write_generated_mapping_to_file

def align_to_dummy_fallback(mapping: Mapping, io: str = 'in', write_to_file: bool = False):
    dummy_inventory = ["ɑ", "i", "u", "t", "s", "n"]
    display_name = mapping.kwargs.get('language_name', 'No Language display name in Config')
    config = generate_config(mapping.kwargs[f'{io}_lang'], 'dummy', display_name, display_name)
    default_char = 't'
    if is_ipa(mapping.kwargs[f'{io}_lang']):
        mapping = align_inventories(mapping.inventory(io), dummy_inventory)
    else:
        und_g2p = make_g2p('und', 'und-ipa')
        mapping = [{"in": x, "out": und_g2p(unidecode(x).lower())} for x in mapping.inventory(io)]
        dummy_list = align_inventories([x['out'] for x in mapping], dummy_inventory)
        dummy_dict = {}
        for x in dummy_list:
            if x['in']:
                dummy_dict[x['in']] = x['out']
                
        for x in mapping:
            try:
                x['out'] = dummy_dict[x['out']]
            except KeyError:
                LOGGER.warn(f"We couldn't guess at what {x['in']} means, so it's being replaced with '{default_char}' instead.")
                x['out'] = default_char       
 
    if write_to_file:
        write_generated_mapping_to_file(config, mapping)
    return config, mapping

if __name__ == "__main__":
    test = Mapping(in_lang='git', out_lang='git-ipa')
    dummy_config, dummy_mapping = align_to_dummy_fallback(test, write_to_file=True)