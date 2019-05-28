'''
Class for performing transductions based on correspondences

'''

from typing import List, Pattern, Tuple
from collections import Counter
import random
import re
from g2p.cors import Correspondence


class IOStates():
    ''' Class containing input and output states along of a Transducer along with indices
    '''

    def __init__(self, indices: List[Tuple[Tuple[int, str], Tuple[int, str]]]):
        self.indices = indices
        self._input_states = [io[0] for io in indices]
        self._output_states = [io[1] for io in indices]
        self._input_count = Counter(i[0] for i in self._output_states)
        self._output_count = Counter(i[0] for i in self._output_states)
        self.input_states = [
            io for io in self._input_states if self._input_count[io[0]] == 1]
        self.output_states = [
            io for io in self._output_states if self._output_count[io[0]] == 1]

    def __call__(self):
        return self.indices

    def down(self):
        return ''.join([state[1] for state in self.output_states])

    def up(self):
        return ''.join([state[1] for state in self.input_states])


class Transducer():
    '''Class for performing transductions based on correspondences
    '''

    def __init__(self, cors: List[Correspondence], as_is: bool = False):
        if not as_is:
            # sort by reverse len
            cors = sorted(cors(), key=lambda x: len(x["from"]), reverse=True)
    
        for cor in cors:
            cor['match_pattern'] = self.rule_to_regex(cor)
        self.as_is = as_is
        self.cor_list = cors
        self._index_match_pattern = re.compile('(?<={)\d+(?=})')
        self._char_match_pattern = re.compile('[^0-9\{\}]+(?={\d+})', re.U)

    def __call__(self, to_parse: str, index: bool = False):
        return self.apply_rules(to_parse, index)

    def rule_to_regex(self, rule):
        if rule['before'] is not None:
            before = rule["before"]
        else:
            before = ''
        if rule['after'] is not None:
            after = rule["after"]
        else:
            after = ''
        fromMatch = re.sub(re.compile('{\d+}'), "", rule["from"])
        try:
            ruleRX = re.compile(f"(?<={before})" + fromMatch + f"(?={after})")
        except:
            raise Exception(
                'Your regex is malformed. Escape all regular expression special characters in your conversion table.')
        return ruleRX

    def returnIndex(self, input_index: int, output_index: int, input_string: str, output: str, original_str: str, intermediate_index: List[Tuple[Tuple[int, str]]]):
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
            # breakpoint()
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
        # many-to-many - TODO: should allow for default many-to-many indexing if no explicit, curly-bracket indexing is provided
        if len(input_string) > 1 and len(output) > 1:
            # for input, zip the matching indices, the actual indices relative to the string, and the chars together
            input_chars = [x.group()
                           for x in self._char_match_pattern.finditer(input_string)]
            input_match_indices = [
                x.group() for x in self._index_match_pattern.finditer(input_string)]
            zipped_input = zip(input_match_indices, input_chars)
            inputs = sorted([(imi, input_index + input_match_indices.index(imi), ic)
                             for imi, ic in zipped_input], key=lambda x: x[0])
            # for output, zip the matching indices, the actual indices relative to the string, and the chars together
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
                    if not original_str[inp[1]] == inp[2]:
                        if not intermediate_index:
                            breakpoint()
                        inp = ('intermediate', intermediate_index[0][0][0], intermediate_index[0][0][1])
                    relation = (inp[1:], outp[1:])
                    relations.append(relation)
            else:
                for outp in outputs:
                    index = outputs.index(outp)
                    try:
                        inp = inputs[index][1:]
                    except IndexError:
                        inp = inputs[len(inputs)-1][1:]
                    if not original_str[inp[0]] == inp[1]:
                        inp = intermediate_index[0][0]
                    relation = (inp, outp[1:])
                    relations.append(relation)
            # return [x for x in relations if original_str[x[0][0]] == x[0][1]]
            return relations
    
    def get_index_length(self, new_index):
        return (len(set([x[0] for x in new_index])), len(set([x[1] for x in new_index])))

    def apply_rules(self, to_parse: str, index: bool = False):
        indices = []
        parsed = to_parse
        if index:
            input_index = 0
            output_index = 0
            for char in range(len(parsed)):
                # account for many-to-many rules making the input index outpace the char-by-char parsing
                if char < input_index:
                    continue
                rule_applied = False
                # go through rules
                for cor in self.cor_list:
                    # find all matches.
                    for match in cor['match_pattern'].finditer(parsed):
                        match_index = match.start()
                        # if start index of match is equal to input index, then apply the rule and append the index-formatted tuple to the main indices list
                        if match_index == input_index:
                            output_sub = re.sub(re.compile('{\d+}'), '', cor['to'])
                            # parse the final output
                            parsed = re.sub(cor['match_pattern'], output_sub, parsed)
                            if not rule_applied:
                                new_index = []
                            non_null_index = self.returnIndex(
                                input_index, output_index, cor['from'], cor['to'], to_parse, new_index)
                            if non_null_index:
                                rule_applied = True
                                new_index = non_null_index
                            else:
                                breakpoint()
                        # if you've gone past the input_index, you can safely break from the loop
                        elif match_index > input_index:
                            break
                
                # increase the index counters
                if rule_applied and len(new_index) > 0:
                    indices += new_index
                    index_lengths = self.get_index_length(new_index)
                    if len(match.group()) > 0:
                        input_index += index_lengths[0]
                    else:
                        input_index += 1
                    if len(output_sub) > 0:
                        output_index += index_lengths[1]
                    else:
                        output_index += 1
                else:
                    # if a rule wasn't applied, just add on the input character as the next input and output character
                    indices.append((
                        (input_index, to_parse[input_index]),  # input
                        (output_index, to_parse[input_index])  # output
                    ))
                    input_index += 1
                    output_index += 1
        else:
            for cor in self.cor_list:
                output_sub = re.sub(re.compile('{\d+}'), '', cor['to'])
                if re.search(cor["match_pattern"], parsed):
                    parsed = re.sub(
                        cor["match_pattern"], output_sub, parsed)
        if index:
            return (parsed, IOStates(indices))
        return parsed
