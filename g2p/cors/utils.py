from collections import defaultdict

def flatten_abbreviations(data):
    dd = defaultdict(list)
    for line in data:
        if line[0]:
            dd[line[0]].extend([l for l in line[1:] if l])
    return dd