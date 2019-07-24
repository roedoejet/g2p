'''
Class for performing transductions based on mappings

'''

from typing import List, Pattern, Tuple, Union
from collections import Counter, OrderedDict
from collections.abc import Iterable
from copy import deepcopy
import re
from g2p.mappings import Mapping
from g2p.mappings.utils import create_fixed_width_lookbehind

class IOStates():
    ''' Class containing input and output states along of a Transducer along with indices
    '''

    def __init__(self, indices: List[Tuple[Tuple[int, str], Tuple[int, str]]]):
        self.indices = indices
        self._input_states = sorted(
            [io[0] for io in indices], key=lambda x: x[0])
        self._output_states = sorted(
            [io[1] for io in indices], key=lambda x: x[0])
        self.condensed_input_states = [
            list(v) for v in dict(self._input_states).items()]
        self.condensed_output_states = [
            list(v) for v in dict(self._output_states).items()]

    def __call__(self):
        return self.indices
    
    def __add__(self, other):
        return IOStates(self.indices + other.indices)

    def __iadd__(self, other):
        return IOStates(self.indices + other.indices)

    def __iter__(self):
        return iter(self.indices)

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

    def __iter__(self):
        return iter(self.states)

    def unpack_states(self, seq):
        states = []
        for state in seq.states:
            if isinstance(state, IOStates):
                states.append(state)
            if isinstance(state, Iterable) and any([isinstance(x, IOStates) for x in state]):
                states += self.unpack_states(state)
        return states

    def compose_states(self, s1, s2):
        inputs = []
        output_i = 0
        for io in s1:
            if io[1][0] != output_i:
                inputs.append(io[0][0])
                output_i = io[1][0]
        inputs.append(len(s1.condensed_input_states))
        outputs = []
        input_i = 0
        output_i = 0
        for io in s2:
            if io[0][0] != input_i:
                outputs.append(output_i)
                input_i = io[0][0]
            output_i = io[1][0]
        outputs.append(len(s2.condensed_output_states))
        if len(inputs) != len(outputs):
            raise TypeError("Sorry, something went wrong. Try checking the two IOStates objects you're trying to compose")
        return list(zip(inputs, outputs))

    def input(self):
        return self.states[0].input()
    
    def output(self):
        return self.states[-1].output()
    
    def composed(self):
        return self.compose_states(self.states[0], self.states[-1])

class Transducer():
    ''' A class for performing transductions based on mappings


    Attributes
    ----------

    mapping: Mapping
        Formatted input/output pairs using the g2p.mappings.Mapping class

    as_is: bool
        Determines whether to evaluate g2p rules in mapping in the order they are, or
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

    def __call__(self, to_parse: str, index: bool = False, debugger: bool = False, output_delimiter: str = ''):
        return self.apply_rules(to_parse, index, debugger, output_delimiter)

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

    def return_index(self, input_index: int, output_index: int,
                     input_string: str, output: str, original_str: str,
                     intermediate_index: List[Tuple[Tuple[int, str]]]):
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

        @param intermediate_index: List[Tuple[Tuple[int, str]]]
            This is a list of any intermediate indices for the current
            input character in the parent loop


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

         """
        if not self.case_sensitive:
            original_str = original_str.lower()
        # (n)one-to-(n)one
        if len(input_string) <= 1 and len(output) <= 1:
            inp = (input_index, input_string)
            outp = (output_index, output)
            if not original_str[inp[0]] == inp[1]:
                try:
                    return [(intermediate_index[0][0], outp)]
                except:
                    breakpoint()
            else:
                return [(inp, outp)]
        # (n)one-to-many
        if len(input_string) <= 1 and len(output) > 1:
            new_index = []
            # when an output character is added to the index, remove it
            # so that it doesn't index the wrong letter if it's a duplicate
            # ie. t -> TT will mistakenly produce [((0,t),(0,T)), ((0,t),(0,T))]
            # instead of [((0,t),(0,T)), ((0,t),(1,T))] unless it is removed
            chars_removed = []
            inp = (input_index, input_string)
            if not original_str[inp[0]] == inp[1]:
                inp = intermediate_index[0][0]
            for output_char in output:
                outp_char_index = output.index(output_char)
                outp = (output_index + outp_char_index + len(chars_removed), output_char)
                new_index.append((inp, outp))
                chars_removed.append(output[outp_char_index])
                output = output[:outp_char_index] + output[outp_char_index+1:]
            return new_index
        # many-to-(n)one
        if len(input_string) > 1 and len(output) <= 1:
            new_index = []
            chars_removed = []
            outp = (output_index, output)
            if not original_str[input_index:].startswith(input_string):
                inp = intermediate_index[0][0]
                new_index.append((inp, outp))
            else:
                for input_char in input_string:
                    inp_char_index = input_string.index(input_char)
                    inp = (input_index + inp_char_index + len(chars_removed), input_char)
                    new_index.append((inp, outp))
                    chars_removed.append(input_string[inp_char_index])
                    input_string = input_string[:inp_char_index] + input_string[inp_char_index+1:]
            return new_index
        # many-to-many -
        # TODO: should allow for default many-to-many indexing if no explicit,
        # curly-bracket indexing is provided
        if len(input_string) > 1 and len(output) > 1:
            # for input, zip the matching indices, the actual indices relative to the string,
            # and the chars together
            input_chars = [x.group()
                           for x in self._char_match_pattern.finditer(input_string)]
            input_match_indices = [
                x.group() for x in self._index_match_pattern.finditer(input_string)]
            zipped_input = zip(input_match_indices, input_chars)
            inputs = sorted([(imi, input_index + input_match_indices.index(imi), ic)
                             for imi, ic in zipped_input], key=lambda x: x[0])
            # for output, zip the matching indices, the actual indices relative to the string,
            # and the chars together
            output_chars = [x.group()
                            for x in self._char_match_pattern.finditer(output)]
            output_match_indices = [
                x.group() for x in self._index_match_pattern.finditer(output)]
            zipped_output = zip(output_match_indices, range(
                len(output_chars)), output_chars)
            outputs = sorted([(omi, output_index + oi, oc)
                              for omi, oi, oc in zipped_output], key=lambda x: x[0])
            # zip i/o according to match index and remove match index
            relations = []
            if len(inputs) >= len(outputs):
                for inp in inputs:
                    index = inputs.index(inp)
                    try:
                        outp = outputs[index]
                    except IndexError:
                        outp = outputs[len(outputs)-1]
                    if not original_str[inp[1]:].startswith(inp[2]):
                        inp = ('intermediate', intermediate_index[0][0][0],
                               intermediate_index[0][0][1])
                    relation = (inp[1:], outp[1:])
                    relations.append(relation)
            else:
                for outp in outputs:
                    index = outputs.index(outp)
                    try:
                        inp = inputs[index][1:]
                    except IndexError:
                        inp = inputs[len(inputs)-1][1:]
                    if not original_str[inp[0]:].startswith(inp[1]):
                        inp = intermediate_index[0][0]
                    relation = (inp, outp[1:])
                    relations.append(relation)
            return relations

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

    def apply_rules(self, to_parse: str, index: bool = False, debugger: bool = False, output_delimiter: str = '') -> Union[str, Tuple[str, IOStates]]:
        """ Apply all the rules in self.mapping sequentially.

        @param to_parse: str
            This is the string to convert

        @param index: bool
            This is whether to preserve indices, default is False

        @param debugger: bool
            This is whether to show intermediary steps, default is False

         @param output_delimiter: str
            This is whether to insert a delimiter between each conversion, default is an empty string

        """
        indices = []
        rules_applied = []

        # initialized parsed
        parsed = to_parse

        if index:
            input_index = 0
            output_index = 0
            for char in range(len(to_parse)):
                # set intermediate parsed
                intermediate_parsed = to_parse
                # account for many-to-many rules making the input index
                # outpace the char-by-char parsing
                if char < input_index:
                    continue
                rule_applied = False
                # go through rules
                for io in self.mapping:
                    io_copy = deepcopy(io)
                    # find all matches.
                    for match in io_copy['match_pattern'].finditer(intermediate_parsed):
                        match_index = match.start()
                        # if start index of match is equal to input index,
                        # then apply the rule and append the index-formatted tuple
                        # to the main indices list
                        if match_index == input_index:
                            if output_delimiter:
                                # Don't add the delimiter to the last segment
                                if not char >= len(to_parse) -1:
                                    io_copy['out'] += output_delimiter
                            # parse the final output
                            output_sub = re.sub(
                                re.compile(r'{\d+}'), '', io_copy['out'])
                            inp = intermediate_parsed
                            outp = re.sub(
                                io_copy["match_pattern"], output_sub, intermediate_parsed)
                            if debugger and inp != outp:
                                applied_rule = {"input": inp,
                                                "rule": io_copy, "output": outp}
                                rules_applied.append(applied_rule)
                            intermediate_parsed = outp
                            # if no rule has yet applied, the new index is empty
                            if not rule_applied:
                                new_index = []
                            # get the new index tuple
                            non_null_index = self.return_index(
                                input_index, output_index, io_copy['in'], io_copy['out'],
                                to_parse, new_index)
                            # if it's not empty, then a rule has applied and it can overwrite
                            # the previous intermediate index tuple
                            if non_null_index:
                                rule_applied = True
                                new_index = non_null_index
                        # if you've gone past the input_index, you can safely break from the loop
                        elif match_index > input_index:
                            break
                # increase the index counters
                # if the rule applied
                if rule_applied and new_index:
                    # add the new index to the list of indices
                    indices += new_index
                    # get the length of the new index inputs and outputs
                    index_lengths = self.get_index_length(new_index)
                    # increase the input counter by the length of the input
                    if match.group():
                        input_index += index_lengths[0]
                    else:
                        input_index += 1
                    # increase the output counter by the length of the input
                    if output_sub:
                        output_index += index_lengths[1]
                    else:
                        output_index += 1
                else:
                    # if a rule wasn't applied, just add on the input character
                    # as the next input and output character
                    indices.append((
                        (input_index, to_parse[input_index]),  # input
                        (output_index, to_parse[input_index])  # output
                    ))
                    input_index += 1
                    output_index += 1
        else:
            # if not worrying about indices, just do the conversion rule-by-rule
            for io in self.mapping:
                io_copy = deepcopy(io)
                if output_delimiter:
                    # Don't add the delimiter to the last segment
                    if not char >= len(to_parse) -1:
                        io_copy['out'] += output_delimiter
                output_sub = re.sub(re.compile(r'{\d+}'), '', io_copy['out'])
                if re.search(io_copy["match_pattern"], parsed):
                    inp = parsed
                    outp = re.sub(
                        io_copy["match_pattern"], output_sub, parsed)
                    if debugger and inp != outp:
                        applied_rule = {"input": inp,
                                        "rule": io_copy, "output": outp}
                        rules_applied.append(applied_rule)
                    parsed = outp
        if index and debugger:
            io_states = IOStates(indices)
            return (io_states.output(), io_states, rules_applied)
        if debugger:
            return (parsed, rules_applied)
        if index:
            io_states = IOStates(indices)
            return (io_states.output(), io_states)
        return parsed


class CompositeTransducer():
    ''' Class containing one or more Transducers

    Attributes
    ----------

    transducers: List[Transducer]
        Ordered list of Transducer objects to concatenate.

    '''

    def __init__(self, transducers: List[Transducer]):
        self._transducers = transducers

    def __call__(self, to_parse: str, index: bool = False, debugger: bool = False):
        return self.apply_rules(to_parse, index, debugger)

    def apply_rules(self, to_parse: str, index: bool = False, debugger: bool = False):
        parsed = to_parse
        indexed = []
        debugged = []
        for transducer in self._transducers:
            response = transducer(parsed, index, debugger)
            if index:
                indexed += response[1]
                if debugger:
                    debugged += response[2]
            if debugger:
                debugged += response[1]
            if index or debugger:
                parsed = response[0]
            else:
                parsed = response
        if index and debugger:
            return (parsed, indexed, debugged)
        if index:
            return (parsed, indexed)
        if debugger:
            return (parsed, debugged)
        return parsed
