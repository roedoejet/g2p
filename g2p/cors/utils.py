def flatten_abbreviations(data):
    return [{"abbreviation": line[0], "stands_for": line[1:]} for line in data if line[0]]