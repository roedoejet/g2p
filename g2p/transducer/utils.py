from typing import Dict, List, Pattern, Tuple, Union

def return_default_mapping(input_strings: List[str], output_strings: List[str],
                            input_index_offsets: List[int], output_index_offsets: List[int]):
    ''' This function takes an arbitrary number of input & output strings and their corresponding index offsets.
        It then zips them up 1 by 1. If the input is longer than the output or vice versa, it continues zipping
        using the last item of either input or output respectively.
    '''
    new_input = {}
    # go through each input or output whichever is longer
    for i in range(0, max(len(input_strings), len(output_strings))):
        try:
            input_i = input_index_offsets[i]
        except IndexError:
            input_i = input_index_offsets[-1]
        try:
            output_i = output_index_offsets[i]
        except IndexError:
            output_i = output_index_offsets[-1]
        try:
            # if inputs and outputs are the same length, just zip them up
            new_input[input_i] = {'input_string': input_strings[i],
                                    'output': {output_i: output_strings[i]}}
        except IndexError:
            # but if the input is longer than output, use the last output character
            if len(input_strings) > len(output_strings):
                new_input[input_i] = {'input_string': input_strings[i],
                                        'output': {output_i: output_strings[-1]}}
            # conversely if the output is longer than input, use the last input character
            elif len(input_strings) < len(output_strings):
                if input_i in new_input:
                    intermediate_output = new_input[input_i]['output']
                else:
                    intermediate_output = {}
                new_input[input_i] = {'input_string': input_strings[-1],
                                        'output': {**intermediate_output, **{output_i: output_strings[i]}}}
    return new_input

def convert_index_to_tuples(index):
    container = []
    for input_index, val in index.items():
        input_string = val['input_string']
        for output_index, output_string in val['output'].items():
            container.append(((input_index, input_string),
                                (output_index, output_string)))
    return container

def convert_tuples_to_index(tuples, reverse=False):
    indices = {}
    for tup in tuples:
        if reverse:
            inp = tup[1]
            outp = tup[0]
        else:
            inp = tup[0]
            outp = tup[1]
        if inp[0] in indices:
            intermediate_output = indices[inp[0]].get('output', {})
        else:
            intermediate_output = {}
        indices[inp[0]] = {'input_string': inp[1],
                            'output': {**intermediate_output, **{outp[0]: outp[1]}}}
    return indices