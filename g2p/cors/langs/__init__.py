import os

LANGS = {}

for root, dirs, files in os.walk(os.path.dirname(__file__)):
    for folder in dirs:
        if folder != "__pycache__":
            for subroot, subdirs, subfiles in os.walk(os.path.join(root, folder)):
                LANGS[folder] = {os.path.splitext(f)[0]: os.path.join(subroot, f) for f in subfiles}
