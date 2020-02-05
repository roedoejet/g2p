'''
    This module helps validate mapping objects for the purpose of debugging
'''

import re

from typing import List

from g2p.mappings import Mapping

def check_bleeding(mapping: Mapping) -> List[dict]:
    """Checks if a mapping contains a bleeding relationship

    This might be intentional, but it flags them for easier debugging.

    Example:
        Counterbleeding order ( ab -> c ):
            { "in": "ab", "out": "c" }
            { "in": "a", "out": "b" }
        Bleeding order ( ab -> bb ):
            { "in": "a", "out": "b" }
            { "in": "ab", "out": "c" }
    
    Args:
        mapping (Mapping): The mapping to check
    
    Returns:
        List[dict]: List of bleeding relationships
    """
    pass

def check_feeding(mapping: Mapping) -> List[dict]:
    """Checks if a mapping contains a feeding relationship

    This might be intentional, but it flags them for easier debugging.
    Finds all input/output pairs whose output is matched with the input of a subsequent rule.

    Example:
        Counterfeeding order ( ab -> adb ):
            { "in": "a", "out": "ad"}
            { "in": "ab", "out": "ac"}
        Feeding order ( ab -> adc ):
            { "in": "ab", "out": "ac"}
            { "in": "a", "out": "ad"}
    
    Args:
        mapping (Mapping): The mapping to check
    
    Returns:
        List[dict]: List of feeding relationships
    """
    to_check = []
    input_match_patterns = [io['match_pattern'] for io in mapping]
    outputs = [io['out'] for io in mapping]
    for out_i, outp in enumerate(outputs):
        for in_i, inp in enumerate(input_match_patterns[out_i+1:]):
            if re.search(inp, outp):
                # exclude unnecessary feeding
                if mapping[out_i]['in'] != mapping[out_i]['out'] and mapping[in_i+1+out_i]['in'] != mapping[in_i+1+out_i]['out']:
                    to_check.append({'feeding': mapping[out_i], 'fed': mapping[in_i+1+out_i]})
    return to_check

def check_unnecessary(mapping: Mapping):
    """Checks if a mapping contains unnecessary rules (x -> x)
    
    Args:
        mapping (Mapping): [description]
    """
    to_check = []
    for io in mapping:
        if io['in'] == io['out']:
            to_check.append(io)
    return to_check

def check_default_ordering(mapping: Mapping):
    to_check = []
    pass