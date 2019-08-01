import os
import yaml

# LANGS = {}

with open(os.path.join(os.path.dirname(__file__), 'langs.yml'), encoding='utf-8') as f:
    try:
        LANGS = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        print(exc)