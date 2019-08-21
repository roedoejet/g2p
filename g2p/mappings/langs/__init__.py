import os
import pickle
from copy import deepcopy
from pathlib import Path
import timeit
import yaml

from g2p.mappings.utils import load_from_file
from g2p import exceptions
LANGS_DIR = os.path.dirname(__file__)

def cache_langs():
    ''' Read in all files and save as pickle
    '''
    langs = {}
    dir_path = Path(LANGS_DIR)
    paths = dir_path.glob('./*/config.y*ml')
    for path in paths:
        code = path.parent.stem
        with open(path) as f:
            data = yaml.safe_load(f)
        # Allow for a single map in a configuration
        if not 'mappings' in data:
            try:
                mapping['mapping_data'] = load_from_file(os.path.join(LANGS_DIR, code, data['mapping']))
            except KeyError:
                # Is "mapping" key missing?
                raise exceptions.MalformedMapping()
        # Else, there is more than one mapping, under 'mappings' key
        else:
            for mapping in data['mappings']:
                try:
                    mapping['mapping_data'] = load_from_file(os.path.join(LANGS_DIR, code, mapping['mapping']))
                except KeyError:
                    # Is "mapping" key missing?
                    raise exceptions.MalformedMapping()
        langs = {**langs, **{code: data}}
    with open(LANGS_PKL, 'wb') as f:
        pickle.dump(langs, f)
    return langs


LANGS_PKL = os.path.join(LANGS_DIR, 'langs.pkl')

# Cache mappings as pickle file for quick loading
with open(LANGS_PKL, 'rb') as f:
    LANGS = pickle.load(f)
    
LANGS_AVAILABLE = [{k: v['language_name']} for k, v in LANGS.items()]
MAPPINGS_AVAILABLE = [mapping for k, v in LANGS.items() for mapping in v['mappings']]

if __name__ == "__main__":
    cache_langs()