'''
Class for performing transductions based on mappings

'''

import re
import copy
from typing import Dict, List, Pattern, Tuple, Union
from collections import OrderedDict
from collections.abc import Iterable
from g2p.mappings import Mapping
from g2p.mappings.utils import create_fixed_width_lookbehind, normalize
from g2p.exceptions import MalformedMapping
from g2p.log import LOGGER
from g2p.transducer.indices import Indices, IndexSequence
from g2p.transducer.utils import return_default_mapping

# Avoid TypeError in Python < 3.7 (see
# https://stackoverflow.com/questions/6279305/typeerror-cannot-deepcopy-this-pattern-object)
copy._deepcopy_dispatch[type(re.compile(''))] = lambda r, _: r


class Transducer():
    ''' A class for performing transductions based on mappings


    Attributes
    ----------

    mapping: Mapping
        Formatted input/output pairs using the g2p.mappings.Mapping class

    _index_match_pattern: Pattern
        Pattern to match the digit inside curly brackets { } as is this package's convention

    _char_match_pattern: Pattern
        Pattern to match the character(s) preceding the _index_match_pattern

    '''

    def __init__(self, mapping: Mapping):
        self.mapping = mapping
        self.case_sensitive = mapping.kwargs['case_sensitive']
        self.norm_form = mapping.kwargs.get('norm_form', 'none')
        self.out_delimiter = mapping.kwargs.get('out_delimiter', '')
        self._index_match_pattern = re.compile(r'(?<={)\d+(?=})')
        self._char_match_pattern = re.compile(r'[^0-9\{\}]+(?={\d+})', re.U)

    def __repr__(self):
        return f"{__class__} between {self.mapping.kwargs['in_lang']} and {self.mapping.kwargs['out_lang']}"

    def __call__(self, to_convert: str, index: bool = False, debugger: bool = False):
        return self.apply_rules(to_convert, index, debugger)

    def strings_to_lists(self, input_string: str, output_string: str,
                         input_index: int, output_index: int):
        ''' Create default lists
        '''
        # separate string into chars
        default_inputs = [x for x in input_string]
        default_outputs = [x for x in output_string]
        # get offsets for each char
        default_input_offsets = [
            i + input_index for i, v in enumerate(default_inputs)]
        default_output_offsets = [
            i + output_index for i, v in enumerate(default_outputs)]
        default_index = return_default_mapping(
            default_inputs, default_outputs, default_input_offsets, default_output_offsets)
        return default_index

    def return_index(self, input_index: int, output_index: int,
                     input_string: str, output_string: str, original_str: str,
                     intermediate_index: dict) -> Dict[int, Dict[str, str]]:
        """ Return a dictionary containing input indices as keys.

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

        TODO: potentially refactor this to lean more on the return_default_mapping method
         """
        intermediate_index = copy.deepcopy(intermediate_index)
        # (n)one-to-(n)one
        if len(input_string) <= 1 and len(output_string) <= 1:
            # create output dictionary
            new_output = {}
            new_output[output_index] = output_string
            # attach it to intermediate_index and merge output
            intermediate_output = intermediate_index[input_index].get('output', {
            })
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
            # If indices are explicitly listed with {} notation
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
                    # Get strings from inputs if they match the match_index
                    explicit_inputs = [x['string']
                                       for x in inputs if x['match_index'] == match_index]
                    # Get strings from outputs if they match the match_index
                    explicit_outputs = [x['string']
                                        for x in outputs if x['match_index'] == match_index]
                    # Get offset for inputs by adding the length of the input string up to the match
                    # plus the overall input index/offset
                    explicit_input_offsets = [
                        len(''.join([x['string'] for x in inputs[:i]])) + input_index for i, v in enumerate(inputs) if v['match_index'] == match_index]
                    # Get offset for outputs by adding the length of the output string up to the match
                    # plus the overall output index/offset
                    explicit_output_offsets = [
                        len(''.join([x['string'] for x in outputs[:i]])) + output_index for i, v in enumerate(outputs) if v['match_index'] == match_index]
                    # Use default mapping to zip them up
                    explicit_index = return_default_mapping(
                        explicit_inputs, explicit_outputs, explicit_input_offsets, explicit_output_offsets)
                    new_input = {**new_input, **explicit_index}
            # Make sure mapping is valid
            elif any(self._char_match_pattern.finditer(input_string)) or any(self._char_match_pattern.finditer(output_string)):
                raise MalformedMapping()
            # else just use default many-to-many indexing
            else:
                default_index = self.strings_to_lists(
                    input_string, output_string, input_index, output_index)
                new_input = {**new_input, **default_index}
            return {**intermediate_index, **new_input}

    def apply_rules(self, to_convert: str, index: bool = False, debugger: bool = False) -> Union[str, Tuple[str, Indices]]:
        """ Apply all the rules in self.mapping sequentially.

        @param to_convert: str
            This is the string to convert

        @param index: bool
            This is whether to preserve indices, default is False

        @param debugger: bool
            This is whether to show intermediary steps, default is False

        """
        indices = {}
        rules_applied = []

        if not self.case_sensitive:
            to_convert = to_convert.lower()

        if self.norm_form:
            to_convert = normalize(to_convert, self.norm_form)

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
                    io_copy = copy.deepcopy(io)
                    # find all matches.
                    for match in io_copy['match_pattern'].finditer(intermediate_conversion):
                        match_index = match.start()
                        # if start index of match is equal to input index,
                        # then apply the rule and append the index-formatted tuple
                        # to the main indices list
                        if match_index == input_index:
                            if self.out_delimiter:
                                # Don't add the delimiter to the last segment
                                if not char + (len(io_copy['in']) - 1) >= len(to_convert) - 1:
                                    io_copy['out'] += self.out_delimiter
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
                    for v in new_index.values():
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
                io_copy = copy.deepcopy(io)
                if self.out_delimiter:
                    io_copy['out'] += self.out_delimiter
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
            # Don't add the delimiter to the last segment
            converted = converted.rstrip()
        if index and debugger:
            io_states = Indices(indices)
            return (io_states.output(), io_states, rules_applied)
        if debugger:
            return (converted, rules_applied)
        if index:
            io_states = Indices(indices)
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

    def __repr__(self):
        return f"{__class__} between {self._transducers[0].mapping.kwargs['in_lang']} and {self._transducers[-1].mapping.kwargs['out_lang']}"

    def __call__(self, to_convert: str, index: bool = False, debugger: bool = False):
        return self.apply_rules(to_convert, index, debugger)

    def apply_rules(self, to_convert: str, index: bool = False, debugger: bool = False):
        converted = to_convert
        indexed = []
        debugged = []
        for transducer in self._transducers:
            response = transducer(converted, index, debugger)
            if index:
                indexed.append(response[1])
                if debugger:
                    debugged += response[2]
            if debugger:
                debugged += response[1]
            if index or debugger:
                converted = response[0]
            else:
                converted = response
        if index and debugger:
            return (converted, IndexSequence(*indexed), debugged)
        if index:
            return (converted, IndexSequence(*indexed))
        if debugger:
            return (converted, debugged)
        return converted
