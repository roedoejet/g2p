from unidecode import unidecode

from g2p.mappings import Mapping
from g2p.mappings.create_ipa_mapping import align_inventories
from g2p.mappings.utils import generate_config, is_ipa, write_generated_mapping_to_file

def align_to_dummy_fallback(mapping, io: str = 'out', write_to_file: bool = False):
    dummy_inventory = ["ɑ", "i", "u", "t", "s", "n"]
    display_name = mapping.kwargs.get('language_name', 'No Language display name in Config')
    config = generate_config(mapping.kwargs[f'{io}_lang'], 'dummy', display_name, display_name)
    
    if is_ipa(mapping.kwargs[f'{io}_lang']):
        mapping = align_inventories(mapping.inventory(io), dummy_inventory)
    else:
        inventory = [unidecode(x) for x in mapping.inventory(io)]
        mapping = align_inventories(inventory, dummy_inventory)

    if write_to_file:
        write_generated_mapping_to_file(config, mapping)
    return config, mapping

if __name__ == "__main__":
    test = Mapping(in_lang='git', out_lang='git-ipa')
    dummy_config, dummy_mapping = align_to_dummy_fallback(test, io='in', write_to_file=True)