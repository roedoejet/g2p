"""

Utilities used by other classes

"""

from collections import defaultdict
import regex as re


def flatten_abbreviations(data):
    ''' Turn a CSV-sourced list of lists into a flattened DefaultDict
    '''
    default_dict = defaultdict(list)
    for line in data:
        if line[0]:
            default_dict[line[0]].extend([l for l in line[1:] if l])
    return default_dict


def expand_abbreviations(data):
    ''' Exapand a flattened DefaultDict into a CSV-formatted list of lists
    '''
    lines = []
    if data:
        for key in data.keys():
            line = [key]
            for col in data[key]:
                line.append(col)
            lines.append(line)
    return lines


def unicode_escape(text):
    ''' Find any escaped characters and turn them into codepoints
    '''
    return re.sub(r"""\\(u[0-9A-Fa-f]{4}|U[0-9A-Fa-f]{6})""", escape_to_codepoint, text)


def escape_to_codepoint(match):
    ''' Turn escape into codepoint
    '''
    hex_codepoint = match.group(1)[1:]
    return chr(int(hex_codepoint, base=16))


def create_fixed_width_lookbehind(pattern):
    '''Turn all characters into fixed width lookbehinds
    '''
    return re.sub(re.compile(r"""(?<=\(?)[\p{L}\p{M}|]+(?=\)?)""", re.U),
                  pattern_to_fixed_width_lookbehinds, pattern)


def pattern_to_fixed_width_lookbehinds(match):
    ''' Python must have fixed-width lookbehinds.
    '''
    pattern = match.group()
    pattern = sorted(pattern.split('|'), key=len, reverse=True)
    current_len = len(pattern[0])
    all_lookbehinds = []
    current_list = []
    for item in pattern:
        if len(item) == current_len:
            current_list.append(item)
        else:
            current_len = len(item)
            all_lookbehinds.append(current_list)
            current_list = [item]
        if pattern.index(item) == len(pattern) - 1:
            all_lookbehinds.append(current_list)
    all_lookbehinds = [f"(?<={'|'.join(items)})" for items in all_lookbehinds]
    return '(' + '|'.join(all_lookbehinds) + ')'
