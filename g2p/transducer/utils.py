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