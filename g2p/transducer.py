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
        self.input_states = [io for io in self._input_states if self._input_count[io[0]] == 1]
        self.output_states = [io for io in self._output_states if self._output_count[io[0]] == 1]

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
            # process intermediate to prevent feeding
            cors = self.process_intermediate(cors)
            # sort by reverse len
            cors.sort(key=len, reverse=True)

        for cor in cors:
            cor['match_pattern'] = self.rule_to_regex(cor)

        self.cor_list = cors
        self._index_match_pattern = re.compile('(?<={)\d+(?=})')
        self._char_match_pattern = re.compile('\w+(?={\d+})')

    def __call__(self, to_parse: str, index: bool = False):
        return self.apply_rules(to_parse, index)

    def process_intermediate(self, cor_list):
        # To prevent feeding
        for cor in cor_list:
            # if output exists as input for another cor
            if cor['to'] in [temp_cor['from'] for temp_cor in cor_list]:
                # assign a random, unique character as a temporary value. this could be more efficient
                random_char = chr(random.randrange(9632, 9727))
                # make sure character is unique
                if [temp_char for temp_char in cor_list if 'temp' in list(temp_char.keys())]:
                    while random_char in [temp_char['temp'] for temp_char in cor_list if 'temp' in list(temp_char.keys())]:
                        random_char = chr(random.randrange(9632, 9727))
                cor['temp'] = random_char

        # preserve rule ordering with regex, then apply context free changes from largest to smallest
        context_sensitive_rules = [x for x in cor_list if (
            x['before'] != '' or x['after'] != "")]
        context_free_rules = [
            x for x in cor_list if x['before'] == "" and x["after"] == ""]
        context_free_rules.sort(key=lambda x: len(x["from"]), reverse=True)
        cor_list = context_sensitive_rules + context_free_rules
        return cor_list

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
    
    def returnIndex(self, input_index: int, output_index: int, input_string: str, output: str):
        # (n)one-to-(n)one
        if len(input_string) <= 1 and len(output) <= 1:
            inp = (input_index, input_string)
            outp = (output_index, output)
            return [(inp, outp)]
        # (n)one-to-many
        if len(input_string) <= 1 and len(output) > 1:
            # breakpoint()
            new_index = []
            inp = (input_index, input_string)
            for output_char in output:
                outp = (output_index + output.index(output_char), output_char)
                new_index.append((inp, outp))
            return new_index
        # many-to-(n)one
        if len(input_string) > 1 and len(output) <= 1:
            new_index = []
            outp = (output_index, output)
            for input_char in input_string:
                inp = (input_index, input_char)
                new_index.append((inp, outp))
            return new_index
        # many-to-many
        if len(input_string) > 1 and len(output) > 1:
            # pattern for finding indices
            index_pattern = self._index_match_pattern
            # pattern for finding chars before indices
            char_pattern = self._char_match_pattern
            # for input, zip the matching indices, the actual indices relative to the string, and the chars together
            input_chars = [x.group() for x in char_pattern.finditer(input_string)]
            input_match_indices = [x.group() for x in index_pattern.finditer(input_string)]
            zipped_input = zip(input_match_indices, input_chars)
            inputs = sorted([(imi, input_index + input_match_indices.index(imi), ic) for imi, ic in zipped_input], key=lambda x: x[0])
            # for output, zip the matching indices, the actual indices relative to the string, and the chars together
            output_chars = [x.group() for x in char_pattern.finditer(output)]
            output_match_indices = [x.group() for x in index_pattern.finditer(output)]
            zipped_output = zip(output_match_indices, output_chars)
            outputs = sorted([(omi, output_index + output_match_indices.index(omi), oc) for omi, oc in zipped_output], key=lambda x: x[0])
            # zip i/o according to match index and remove match index
            relations = []
            for i in inputs:
                index = inputs.index(i)
                relation = (i[1:], outputs[index][1:])
                relations.append(relation)
            return relations

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
                            rule_applied = True
                            new_index = self.returnIndex(input_index, output_index, cor['from'], cor['to'])
                            indices += new_index
                        # if you've gone past the input_index, you can safely break from the loop
                        elif match_index > input_index:
                            break
                    # if a rule wasn't applied, just add on the input character as the next input and output character
                    if not rule_applied:
                        indices.append((
                            (input_index, to_parse[input_index]), # input
                            (output_index, to_parse[input_index])  # output
                            ))
                # increase the index counters
                if rule_applied:
                    output_sub = re.sub(re.compile('{\d+}'), '', cor['to'])
                    # parse the final output        
                    parsed = re.sub(cor['match_pattern'], output_sub, parsed)
                    if len(match.group()) > 0:
                        input_index += len(match.group())
                    else:
                        input_index += 1
                    if len(output_sub) > 0:
                        output_index += len(output_sub)
                    else:
                        output_index += 1
                else:
                    input_index += 1
                    output_index += 1
        else:
            for cor in self.cor_list:
                if re.search(cor["match_pattern"], parsed):
                    # if a temporary value was assigned
                    if 'temp' in list(cor.keys()):
                        # turn the original value into the temporary one
                        parsed = re.sub(cor["match_pattern"], cor["temp"], parsed)
                    else:
                        parsed = re.sub(
                            cor["match_pattern"], cor["to"], parsed)
            # transliterate temporary values
            for cor in self.cor_list:
                # transliterate temp value to final value if it exists, otherwise pass
                try:
                    if "temp" in cor and cor['temp'] and re.search(cor['temp'], parsed):
                        parsed = re.sub(cor['temp'], cor['to'], parsed)
                    else:
                        pass
                except KeyError:
                    pass
        if index:
            # if parsed != 'pest' and parsed != 'chest':
            #     breakpoint()
            return (parsed, IOStates(indices))
        return parsed
