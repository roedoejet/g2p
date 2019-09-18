import os
import json
import datetime as dt
from copy import deepcopy

import yaml

from g2p.log import LOGGER
from g2p.mappings import Mapping
from g2p.mappings.create_ipa_mapping import align_inventories
from g2p.mappings.utils import generate_config, IndentDumper, write_generated_mapping_to_file

def align_to_dummy_fallback(mapping, io: str = 'out', write_to_file: bool = False):
    dummy_inventory = ["ɑ", "i", "u", "t", "s", "n"]
    display_name = mapping.kwargs.get('language_name', 'No Language display name in Config')
    config = generate_config(mapping.kwargs[f'{io}_lang'], 'dummy', display_name, display_name)
    mapping = align_inventories(mapping.inventory(io), dummy_inventory)
    if write_to_file:
        write_generated_mapping_to_file(config, mapping)
    return config, mapping

if __name__ == "__main__":
    test = Mapping(in_lang='atj', out_lang='atj-ipa')
    dummy_config, dummy_mapping = align_to_dummy_fallback(test, write_to_file=True)