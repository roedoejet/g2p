import os

from unidecode import unidecode

from g2p import make_g2p
from g2p.log import LOGGER
from g2p.mappings import Mapping
from g2p.mappings.create_ipa_mapping import align_inventories
from g2p.mappings.utils import is_ipa, unicode_escape

DUMMY_INVENTORY = ["ɑ", "i", "u", "t", "s", "n"]

def align_to_dummy_fallback(mapping: Mapping, io: str = 'in', write_to_file: bool = False, out_dir: str = ''):
    display_name = mapping.kwargs.get('language_name', 'No Language display name in Config')
    config = {'in_lang': mapping.kwargs[f'{io}_lang'], 'out_lang': 'dummy'}
    default_char = 't'
    if is_ipa(mapping.kwargs[f'{io}_lang']):
        mapping = align_inventories(mapping.inventory(io), DUMMY_INVENTORY)
    else:
        und_g2p = make_g2p('und', 'und-ipa')
        mapping = [{"in": unicode_escape(x), "out": und_g2p(unidecode(x).lower()).output_string} for x in mapping.inventory(io)]
        dummy_list = align_inventories([x['out'] for x in mapping], DUMMY_INVENTORY)
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

    config['mapping'] = mapping
    mapping = Mapping(**config)
    if write_to_file:
        if out_dir:
            if os.path.isdir(out_dir):
                mapping.config_to_file(out_dir)
                mapping.mapping_to_file(out_dir)
            else:
                LOGGER.warning(f'{out_dir} is not a directory. Writing to default instead.')
        else:
            mapping.config_to_file()
            mapping.mapping_to_file()
    return mapping

if __name__ == "__main__":
    test = Mapping(in_lang='git', out_lang='git-ipa')
    dummy_config, dummy_mapping = align_to_dummy_fallback(test, write_to_file=True)
