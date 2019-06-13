from collections import defaultdict

def flatten_abbreviations(data):
    dd = defaultdict(list)
    for line in data:
        if line[0]:
            dd[line[0]].extend([l for l in line[1:] if l])
    return dd

def expand_abbreviations(data):
    lines = []
    for key in data.keys():
        line = [key]
        for col in data[key]:
            line.append(col)
        lines.append(line)
    return lines
