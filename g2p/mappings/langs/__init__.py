import os
import yaml
from copy import deepcopy

# LANGS = {}

with open(os.path.join(os.path.dirname(__file__), 'langs.yml'), encoding='utf-8') as f:
    try:
        LANGS = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        print(exc)

LANGS_AVAILABLE = [{x['code']: x['name']} for x in LANGS]

TABLES_AVAILABLE = []
for lang in LANGS:
    new_lang = {}
    for k, v in deepcopy(lang).items():
        if k == 'code':
            current_lang = v
            new_lang[v] = []
        if k == 'tables':
            new_lang[current_lang] += [x['name'] for x in v]
    TABLES_AVAILABLE.append(new_lang)
