'''
Class for performing transductions based on mappings

'''

from typing import List, Pattern, Tuple, Union
from collections import Counter, OrderedDict
from collections.abc import Iterable
from copy import deepcopy
import re
from gi2pi.mappings import Mapping
from gi2pi.mappings.utils import create_fixed_width_lookbehind
from gi2pi.exceptions import MalformedMapping
from gi2pi.log import LOGGER


class IOStates():
    ''' Class containing input and output states along of a Transducer along with indices
    '''

    def __init__(self, index: Union[dict, List[Tuple[Tuple[int, str], Tuple[int, str]]]]):
        if isinstance(index, dict):
            self.indices = self.convert_index_to_tuples(index)
        else:
            self.indices = index
        self._input_states = sorted(
            [io[0] for io in self.indices], key=lambda x: x[0])
        self._output_states = sorted(
            [io[1] for io in self.indices], key=lambda x: x[0])
        self.condensed_input_states = [
            list(v) for v in dict(self._input_states).items()]
        self.condensed_output_states = [
            list(v) for v in dict(self._output_states).items()]

    def __repr__(self):
        return f"{self.__class__} object with input '{self.input()}' and output '{self.output()}'"

    def __call__(self):
        return self.indices

    def __add__(self, other):
        return IOStates(self.indices + other.indices)

    def __iadd__(self, other):
        return IOStates(self.indices + other.indices)

    def __iter__(self):
        return iter(self.indices)

    def convert_index_to_tuples(self, index):
        try:
            container = []
            for input_index, val in index.items():
                input_string = val['input_string']
                for output_index, output_string in val['output'].items():
                    container.append(((input_index, input_string),
                                      (output_index, output_string)))
            return container
        except:
            breakpoint()

    def convert_tuples_to_index(self, tuples, reverse=False):
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

    def reduced(self):
        reduced = []
        intermediate_index = {
            'in': self.indices[0][0][0], 'out': self.indices[0][1][0]}
        for io in self.indices:
            inp = io[0][0] + 1
            outp = io[1][0]
            if inp == intermediate_index['in'] and outp > intermediate_index['out']:
                intermediate_index['out'] = outp
            if inp > intermediate_index['in'] and outp <= intermediate_index['out']:
                intermediate_index['in'] = inp
            if inp > intermediate_index['in'] and outp > intermediate_index['out']:
                reduced.append(intermediate_index)
                intermediate_index = {'in': inp, 'out': outp}
        reduced.append({"in": len(self.condensed_input_states),
                        "out": len(self.condensed_output_states)})
        reduced = [(x['in'], x['out']) for x in reduced]
        return reduced

    def input(self):
        """ Return the input of a given transduction
        """
        return ''.join([state[1] for state in self.condensed_input_states])

    def output(self):
        """ Return the output of a given transduction
        """
        return ''.join([state[1] for state in self.condensed_output_states])


class IOStateSequence():
    '''Class containing a sequence of IO States
    '''

    def __init__(self, *args: IOStates):
        self.states = []
        for arg in args:
            if isinstance(arg, IOStates):
                self.states.append(arg)
            if isinstance(arg, IOStateSequence):
                self.states += self.unpack_states(arg)
        # breakpoint()

    def __iter__(self):
        return iter(self.states)

    def __repr__(self):
        return f"{self.__class__} object with input '{self.input()}' and output '{self.output()}'"

    def unpack_states(self, seq):
        states = []
        for state in seq.states:
            if isinstance(state, IOStates):
                states.append(state)
            if isinstance(state, Iterable) and any([isinstance(x, IOStates) for x in state]):
                states += self.unpack_states(state)
        return states

    def composed(self, s1, s2):
        # the two states being composed must match
        if len(s1.condensed_output_states) != len(s2.condensed_input_states):
            LOGGER.warning(
                "Sorry, something went wrong. Try checking the two IOStates objects you're trying to compose")
        composed = []
        for io_1 in s1:
            s1_in = io_1[0]
            s1_out = io_1[1]
            for io_2 in s2:
                s2_in = io_2[0]
                s2_out = io_2[1]
                if s2_in[0] == s1_out[0]:
                    composed.append((s1_in, s2_out))
        return IOStates(composed)

    def input(self):
        return self.states[0].input()

    def output(self):
        return self.states[-1].output()

    def reduced(self):
        ''' This is a reduced tuple-based format for indices. It requires that IOStates in the
        IOStateSequence be composed, and then they can be reduced to a list of tuples where each
        tuple contains an input and output index corresponding with that character. The list is equal
        to the length of unique characters
        '''
        composed_states = self.composed(self.states[0], self.states[1])
        counter = 2
        while counter < len(self.states):
            composed_states = self.composed(
                composed_states, self.states[counter])
            counter += 1
        return composed_states.reduced()


class Transducer():
    ''' A class for performing transductions based on mappings


    Attributes
    ----------

    mapping: Mapping
        Formatted input/output pairs using the gi2pi.mappings.Mapping class

    as_is: bool
        Determines whether to evaluate gi2pi rules in mapping in the order they are, or
        to reverse sort them by length

    _index_match_pattern: Pattern
        Pattern to match the digit inside curly brackets { } as is this package's convention

    _char_match_pattern: Pattern
        Pattern to match the character(s) preceding the _index_match_pattern


    Methods
    -------

    rule_to_regex(rule: str) -> Pattern:
        Turns an input string (and the context) from an input/output pair
        into a regular expression pattern



    '''

    def __init__(self, mapping: Mapping, as_is: bool = False):
        self.mapping = mapping
        self.case_sensitive = mapping.case_sensitive
        self.as_is = as_is
        if not self.as_is:
            # sort by reverse len
            self.mapping = sorted(self.mapping(), key=lambda x: len(
                x["in"]), reverse=True)
        # turn "in" in to Regex
        for io in self.mapping:
            io['match_pattern'] = self.rule_to_regex(io)

        self._index_match_pattern = re.compile(r'(?<={)\d+(?=})')
        self._char_match_pattern = re.compile(r'[^0-9\{\}]+(?={\d+})', re.U)

    def __call__(self, to_convert: str, index: bool = False, debugger: bool = False, output_delimiter: str = ''):
        return self.apply_rules(to_convert, index, debugger, output_delimiter)

    def rule_to_regex(self, rule: str) -> Pattern:
        """Turns an input string (and the context) from an input/output pair
        into a regular expression pattern"""
        if "context_before" in rule and rule['context_before']:
            before = rule["context_before"]
        else:
            before = ''
        if 'context_after' in rule and rule['context_after']:
            after = rule["context_after"]
        else:
            after = ''
        input_match = re.sub(re.compile(r'{\d+}'), "", rule["in"])
        try:
            inp = create_fixed_width_lookbehind(before) + input_match
            if after:
                inp += f"(?={after})"

            if not self.case_sensitive:
                rule_regex = re.compile(inp, re.I)
            else:
                rule_regex = re.compile(inp)

        except:
            raise Exception(
                'Your regex is malformed.')
        return rule_regex

    def return_match_starting_indices(self, match_object_list, match_indices):
        indices = []
        all_matches = [x['match_index'] for x in match_object_list]
        for match_index in match_indices:
            indices.append(len(''.join([match_object_list[i]['string'] for i, v in enumerate(
                all_matches[:match_index])])))
        return indices

    def return_default_mapping(self, input_strings: List[str], output_strings: List[str],
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

    def return_index(self, input_index: int, output_index: int,
                     input_string: str, output_string: str, original_str: str,
                     intermediate_index: dict):
        """ Return a list of new index tuples.

        @param input_index: int
            This is where the input is currently at in the parent loop

        @param output_index: int
            This is where the output is currently at in the parent loop

        @param input_string: str
            This is the input string to convert (can refelct an intermediate stage)

        @param output: str
            This is the output string to convert to

        @param original_str: str
            This is the original input

        @param intermediate_index: dict
            This is a dict containing the intermediate form of the index


        There are four main cases. Empty strings are still treated as having indices,
        which is why the cases are written as (n)one.
        This deals for index-preserving epenthesis and deletion.

        An "index tuple" is a tuple containing an input tuple and an output tuple. (input, output)
        Input/Output tuples contain their index as the first item and the character as the second,
        ie (0, 'x') "x" -> "y" would therefore be ((0, "x"), (0, "y"))

        (1) (n)one-to-(n)one
            Given input x and output y, produce an index tuple of (x,y)

        (2) (n)one-to-many
            Given input x and outputs y, z, produce tuples (x, y) and (x, z)

        (3) many-to-(n)one
            Given inputs x, y and output z, produce tuples (x, z) and (y, z)

        (4) many-to-many
            Given inputs w{1} and x{2} and outputs y{2}, z{1},
            produce tuples (w, z) and (x, y).

        TODO: potentially refactor this to lean more on the return_default_mapping method
         """
        # if input_index == 5 and input_string == 's':
        #     breakpoint()
        intermediate_index = deepcopy(intermediate_index)
        # if input_string == 'ʁ':
        if not self.case_sensitive:
            original_str = original_str.lower()
        # (n)one-to-(n)one
        if len(input_string) <= 1 and len(output_string) <= 1:
            # create output dictionary
            new_output = {}
            new_output[output_index] = output_string
            # attach it to intermediate_index and merge output
            try:
                intermediate_output = intermediate_index[input_index].get('output', {
                })
            except IndexError:
                breakpoint()
            intermediate_index[input_index]['output'] = {**intermediate_output,
                                                         **new_output}
            return intermediate_index

        # (n)one-to-many
        if len(input_string) <= 1 and len(output_string) > 1:
            new_output = {}
            intermediate_output = intermediate_index[input_index].get(
                'output', {})
            for index, output_char in enumerate(output_string):
                new_output[output_index + index] = output_char

            # attach it to intermediate_index and merge output
            if new_output:
                intermediate_index[input_index]['output'] = {**intermediate_output,
                                                             **new_output}
            return intermediate_index

        # many-to-(n)one
        if len(input_string) > 1 and len(output_string) <= 1:
            new_input = {}
            new_output = {output_index: output_string}
            # TODO: do we need intermediate output?
            for index, input_char in enumerate(input_string):
                # prevent feeding rules from leaving traces
                if original_str[index + input_index] == input_char:
                    new_input[input_index + index] = {'input_string': input_char,
                                                      'output': new_output}

            return {**intermediate_index, **new_input}

        # many-to-many
        if len(input_string) > 1 and len(output_string) > 1:
            new_input = {}
            if any(self._char_match_pattern.finditer(input_string)) and any(self._char_match_pattern.finditer(output_string)):
                input_char_matches = [x.group()
                                      for x in self._char_match_pattern.finditer(input_string)]

                input_match_indices = [
                    x.group() for x in self._index_match_pattern.finditer(input_string)]
                inputs = [{'match_index': m, 'string': input_char_matches[i]}
                          for i, m in enumerate(input_match_indices)]
                output_char_matches = [x.group()
                                       for x in self._char_match_pattern.finditer(output_string)]
                output_match_indices = [
                    x.group() for x in self._index_match_pattern.finditer(output_string)]
                outputs = [{'match_index': m, 'string': output_char_matches[i]}
                           for i, m in enumerate(output_match_indices)]

                for match_index in input_match_indices:
                    default_inputs = [x['string']
                                      for x in inputs if x['match_index'] == match_index]
                    default_outputs = [x['string']
                                       for x in outputs if x['match_index'] == match_index]
                    default_input_offsets = self.return_match_starting_indices(
                        inputs, [i + input_index for i, v in enumerate(inputs) if v['match_index'] == match_index])
                    default_output_offsets = self.return_match_starting_indices(
                        outputs, [i + output_index for i, v in enumerate(outputs) if v['match_index'] == match_index])
                    default_index = self.return_default_mapping(
                        default_inputs, default_outputs, default_input_offsets, default_output_offsets)

                    new_input = {**new_input, **default_index}
            elif any(self._char_match_pattern.finditer(input_string)) or any(self._char_match_pattern.finditer(output_string)):
                raise MalformedMapping()
            # if there are no explicit inputs or outputs
            # then just use default many-to-many indexing
            else:
                # go through each input or output whichever is longer
                # for i in range(0, max(len(input_string), len(output_string))):
                default_inputs = [x for x in input_string]
                default_outputs = [x for x in output_string]
                default_input_offsets = [
                    i + input_index for i, v in enumerate(default_inputs)]
                default_output_offsets = [
                    i + output_index for i, v in enumerate(default_outputs)]
                default_index = self.return_default_mapping(
                    default_inputs, default_outputs, default_input_offsets, default_output_offsets)
                new_input = {**new_input, **default_index}
            return {**intermediate_index, **new_input}

    def get_index_length(self, new_index: List[Tuple[Tuple[int, str]]]) -> Tuple[int, int]:
        """ Return how many unique input characters and output characters
            there are in a given index tuple.
        """
        # Use set to remove duplicate inputs/outputs (ie for many-to-one)
        input_indices = set([x[0] for x in new_index])
        output_indices = set([x[1] for x in new_index])
        # Sum the length of the inputs/outputs
        return (sum([len(x[1]) for x in input_indices]), sum([len(x[1]) for x in output_indices]))

    def splice_from_index(self, to_splice, index: Tuple[Tuple[int, str]]) -> str:
        splicing_block = {}
        for io in index:
            key = io[0][0]
            new_value = io[1][1]
            if key in splicing_block:
                splicing_block[key] += new_value
            else:
                splicing_block[key] = new_value
        reverse_sorted = OrderedDict(
            sorted(splicing_block.items(), key=lambda x: x[0]))
        for index, string in reverse_sorted.items():
            to_splice = to_splice[:index] + string + to_splice[index + 1:]
        return to_splice

    def apply_rules(self, to_convert: str, index: bool = False, debugger: bool = False, output_delimiter: str = '') -> Union[str, Tuple[str, IOStates]]:
        """ Apply all the rules in self.mapping sequentially.

        @param to_convert: str
            This is the string to convert

        @param index: bool
            This is whether to preserve indices, default is False

        @param debugger: bool
            This is whether to show intermediary steps, default is False

         @param output_delimiter: str
            This is whether to insert a delimiter between each conversion, default is an empty string

        """
        indices = {}
        rules_applied = []

        # initialized converted
        converted = to_convert

        if index:
            input_index = 0
            output_index = 0
            new_index = {}
            for char in range(len(to_convert)):
                # account for many-to-many rules making the input index
                # outpace the char-by-char conversion
                if char < input_index:
                    continue
                if not char in new_index or new_index[char]['input_string'] != to_convert[char]:
                    input_index = char
                    new_index[char] = {'input_string': to_convert[char],
                                       'output': {}}
                # intermediate form refreshes on each new char
                intermediate_conversion = to_convert
                rule_applied = False
                # go through rules
                for io in self.mapping:
                    io_copy = deepcopy(io)
                    # find all matches.
                    for match in io_copy['match_pattern'].finditer(intermediate_conversion):
                        match_index = match.start()
                        # if start index of match is equal to input index,
                        # then apply the rule and append the index-formatted tuple
                        # to the main indices list
                        if match_index == input_index:
                            if output_delimiter:
                                # Don't add the delimiter to the last segment
                                if not char >= len(to_convert) - 1:
                                    io_copy['out'] += output_delimiter
                            # convert the final output
                            output_sub = re.sub(
                                re.compile(r'{\d+}'), '', io_copy['out'])
                            intermediate_output = intermediate_conversion[:char] + re.sub(
                                io_copy["match_pattern"], output_sub, intermediate_conversion[char:])
                            if debugger and intermediate_conversion != intermediate_output:
                                applied_rule = {"input": intermediate_conversion,
                                                "rule": io_copy, "output": intermediate_output}
                                rules_applied.append(applied_rule)
                            # update intermediate converted form
                            intermediate_conversion = intermediate_output
                            # get the new index tuple
                            non_null_index = self.return_index(
                                input_index, output_index, io_copy['in'], io_copy['out'],
                                to_convert, new_index)
                            # if it's not empty, then a rule has applied and it can overwrite
                            # the previous intermediate index tuple
                            if non_null_index:
                                rule_applied = True
                                new_index = {**new_index, **non_null_index}
                        # if you've gone past the input_index, you can safely break from the loop
                        elif match_index > input_index:
                            break
                # increase the index counters
                # new_index = self.convert_index_to_tuples(new_index)
                # if the rule applied
                if rule_applied and new_index[char]['output']:
                    # add the new index to the list of indices
                    indices = {**indices, **new_index}
                    # get the length of the new index inputs and outputs
                    # and increase the input counter by the length of the input
                    input_index = max(new_index.keys())
                    input_index += 1
                    # do the same with outputs
                    outputs = {}
                    for k, v in new_index.items():
                        outputs = {**outputs, **v['output']}
                    output_index = max(outputs.keys())
                    output_index += 1
                else:
                    # if a rule wasn't applied, just add on the input character
                    # as the next input and output character
                    new_index = {**new_index, **{input_index: {'input_string': to_convert[input_index],
                                                               'output': {output_index: to_convert[input_index]}}}}
                    # merge it
                    indices = {**indices, **new_index}
                    # add one to input and output
                    input_index += 1
                    output_index += 1
        else:
            # if not worrying about indices, just do the conversion rule-by-rule
            for io in self.mapping:
                io_copy = deepcopy(io)
                if output_delimiter:
                    # Don't add the delimiter to the last segment
                    if not char >= len(to_convert) - 1:
                        io_copy['out'] += output_delimiter
                output_sub = re.sub(re.compile(r'{\d+}'), '', io_copy['out'])
                if re.search(io_copy["match_pattern"], converted):
                    inp = converted
                    outp = re.sub(
                        io_copy["match_pattern"], output_sub, converted)
                    if debugger and inp != outp:
                        applied_rule = {"input": inp,
                                        "rule": io_copy, "output": outp}
                        rules_applied.append(applied_rule)
                    converted = outp
        if index and debugger:
            io_states = IOStates(indices)
            return (io_states.output(), io_states, rules_applied)
        if debugger:
            return (converted, rules_applied)
        if index:
            io_states = IOStates(indices)
            return (io_states.output(), io_states)
        return converted


class CompositeTransducer():
    ''' Class containing one or more Transducers

    Attributes
    ----------

    transducers: List[Transducer]
        Ordered list of Transducer objects to concatenate.

    '''

    def __init__(self, transducers: List[Transducer]):
        self._transducers = transducers

    def __call__(self, to_convert: str, index: bool = False, debugger: bool = False):
        return self.apply_rules(to_convert, index, debugger)

    def apply_rules(self, to_convert: str, index: bool = False, debugger: bool = False):
        #TODO: should turn indexed into IOStateSequence
        converted = to_convert
        indexed = []
        debugged = []
        for transducer in self._transducers:
            response = transducer(converted, index, debugger)
            if index:
                indexed += response[1]
                if debugger:
                    debugged += response[2]
            if debugger:
                debugged += response[1]
            if index or debugger:
                converted = response[0]
            else:
                converted = response
        if index and debugger:
            return (converted, indexed, debugged)
        if index:
            return (converted, indexed)
        if debugger:
            return (converted, debugged)
        return converted
