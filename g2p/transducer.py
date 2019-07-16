'''
Class for performing transductions based on correspondences

'''

from typing import List, Pattern, Tuple, Union
from collections import Counter
import re
from g2p.cors import Correspondence
from g2p.cors.utils import create_fixed_width_lookbehind


class IOStates():
    ''' Class containing input and output states along of a Transducer along with indices
    '''

    def __init__(self, indices: List[Tuple[Tuple[int, str], Tuple[int, str]]]):
        self.indices = indices
        self._input_states = sorted([io[0] for io in indices], key=lambda x: x[0])
        self._output_states = sorted([io[1] for io in indices], key=lambda x: x[0])
        self._input_count = Counter(i[0] for i in self._output_states)
        self._output_count = Counter(i[0] for i in self._output_states)
        self.input_states = [
            io for io in self._input_states if self._input_count[io[0]] == 1]
        self.output_states = [
            io for io in self._output_states if self._output_count[io[0]] == 1]

    def __call__(self):
        return self.indices

    def __iadd__(self, other):
        return IOStates(self.indices + other.indices)

    def down(self):
        """ Return the output of a given transduction
        """
        return ''.join([state[1] for state in self.output_states])

    def up(self):
        """ Return the input of a given transduction
        """
        return ''.join([state[1] for state in self.input_states])


class Transducer():
    ''' A class for performing transductions based on correspondences


    Attributes
    ----------

    cors: Correspondence
        Formatted input/output pairs using the g2p.cors.Correspondence class

    as_is: bool
        Determines whether to evaluate g2p rules in cors in the order they are, or
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

    def __init__(self, cor_list: Correspondence, as_is: bool = False):
        if not as_is:
            # sort by reverse len
            cor_list = sorted(cor_list(), key=lambda x: len(
                x["from"]), reverse=True)
        # turn "from" in to Regex
        for cor in cor_list:
            cor['match_pattern'] = self.rule_to_regex(cor)

        self.as_is = as_is
        self.cor_list = cor_list
        self._index_match_pattern = re.compile(r'(?<={)\d+(?=})')
        self._char_match_pattern = re.compile(r'[^0-9\{\}]+(?={\d+})', re.U)

    def __call__(self, to_parse: str, index: bool = False, debugger: bool = False, case_sensitive: bool = True):
        return self.apply_rules(to_parse, index, debugger, case_sensitive)

    def rule_to_regex(self, rule: str) -> Pattern:
        """Turns an input string (and the context) from an input/output pair
        into a regular expression pattern"""
        if rule['before'] is not None:
            before = rule["before"]
        else:
            before = ''
        if rule['after'] is not None:
            after = rule["after"]
        else:
            after = ''
        from_match = re.sub(re.compile(r'{\d+}'), "", rule["from"])
        try:
            rule_regex = re.compile(create_fixed_width_lookbehind(
                before) + from_match + f"(?={after})")
        except:
            breakpoint()
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
        # (n)one-to-(n)one
        if len(input_string) <= 1 and len(output) <= 1:
            inp = (input_index, input_string)
            outp = (output_index, output)
            if not original_str[inp[0]] == inp[1]:
                return [(intermediate_index[0][0], outp)]
            else:
                return [(inp, outp)]
        # (n)one-to-many
        if len(input_string) <= 1 and len(output) > 1:
            new_index = []
            inp = (input_index, input_string)
            if not original_str[inp[0]] == inp[1]:
                inp = intermediate_index[0][0]
            for output_char in output:
                outp = (output_index + output.index(output_char), output_char)
                new_index.append((inp, outp))
            # return [x for x in new_index if original_str[x[0][0]] == x[0][1]]
            return new_index
        # many-to-(n)one
        if len(input_string) > 1 and len(output) <= 1:
            new_index = []
            outp = (output_index, output)
            if not original_str[input_index:].startswith(input_string):
                inp = intermediate_index[0][0]
                new_index.append((inp, outp))
            else:
                for input_char in input_string:
                    inp = (input_index + input_string.index(input_char), input_char)
                    new_index.append((inp, outp))
            # return [x for x in new_index if original_str[x[0][0]] == x[0][1]]
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

    def apply_rules(self, to_parse: str, index: bool = False, debugger: bool = False, case_sensitive: bool = True) -> Union[str, Tuple[str, IOStates]]:
        """ Apply all the rules in self.cor_list sequentially.

        @param to_parse: str
            This is the string to convert

        @param index: bool
            This is whether to preserve indices, default is False

        @param debugger: bool
            This is whether to show intermediary steps, default is False

        """
        indices = []
        if not case_sensitive:
            parsed = to_parse.lower()
        else:
            parsed = to_parse
        rules_applied = []

        if index:
            input_index = 0
            output_index = 0
            for char in range(len(parsed)):
                # account for many-to-many rules making the input index
                # outpace the char-by-char parsing
                if char < input_index:
                    continue
                rule_applied = False
                # go through rules
                for cor in self.cor_list:
                    # find all matches.
                    for match in cor['match_pattern'].finditer(parsed):
                        match_index = match.start()
                        # if start index of match is equal to input index,
                        # then apply the rule and append the index-formatted tuple
                        # to the main indices list
                        if match_index == input_index:
                            # parse the final output
                            output_sub = re.sub(
                                re.compile(r'{\d+}'), '', cor['to'])
                            inp = parsed
                            if not case_sensitive:
                                outp = re.sub(cor["match_pattern"], output_sub, parsed, flags=re.I)
                            else:
                                outp = re.sub(cor["match_pattern"], output_sub, parsed)
                            if debugger and inp != outp:
                                applied_rule = {"input": inp,
                                                "rule": cor, "output": outp}
                                rules_applied.append(applied_rule)
                            parsed = outp
                            # if no rule has yet applied, the new index is empty
                            if not rule_applied:
                                new_index = []
                            # get the new index tuple
                            non_null_index = self.return_index(
                                input_index, output_index, cor['from'], cor['to'],
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
            for cor in self.cor_list:
                output_sub = re.sub(re.compile(r'{\d+}'), '', cor['to'])
                if re.search(cor["match_pattern"], parsed):
                    inp = parsed
                    if not case_sensitive:
                        outp = re.sub(
                            cor["match_pattern"], output_sub, parsed, re.I)
                    else:
                        outp = re.sub(
                            cor["match_pattern"], output_sub, parsed)
                    if debugger and inp != outp:
                        applied_rule = {"input": inp,
                                        "rule": cor, "output": outp}
                        rules_applied.append(applied_rule)
                    parsed = outp
        if index and debugger:
            return (parsed, IOStates(indices), rules_applied)
        if debugger:
            return (parsed, rules_applied)
        if index:
            return (parsed, IOStates(indices))
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
