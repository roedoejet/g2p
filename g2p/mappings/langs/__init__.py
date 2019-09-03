import os
import pickle
from copy import deepcopy
from pathlib import Path
import timeit
import yaml

from g2p.mappings.utils import load_mapping_from_path
from g2p import exceptions
LANGS_DIR = os.path.dirname(__file__)

def cache_langs():
    ''' Read in all files and save as pickle
    '''
    langs = {}
    dir_path = Path(LANGS_DIR)
    # Sort by language code
    paths = sorted(dir_path.glob('./*/config.y*ml'), key=lambda x: x.parent.stem)
    for path in paths:
        code = path.parent.stem
        with open(path) as f:
            data = yaml.safe_load(f)
        # If there is a mappings key, there is more than one mapping
        if 'mappings' in data:
            for index, mapping in enumerate(data['mappings']):
                data['mappings'][index] = load_mapping_from_path(path, index)
        else:
            data = load_mapping_from_path(path)
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