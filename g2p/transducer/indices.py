'''
Class for performing transductions based on mappings

'''
import re
import copy
from typing import List, Tuple, Union
from collections.abc import Iterable

from g2p.transducer.utils import convert_index_to_tuples, convert_tuples_to_index

# Avoid TypeError in Python < 3.7 (see
# https://stackoverflow.com/questions/6279305/typeerror-cannot-deepcopy-this-pattern-object)
copy._deepcopy_dispatch[type(re.compile(''))] = lambda r, _: r

class Indices():
    ''' Class containing input and output states along of a Transducer along with indices
    '''

    def __init__(self, index: Union[dict, List[Tuple[Tuple[int, str], Tuple[int, str]]]]):
        if isinstance(index, dict):
            self.indices = convert_index_to_tuples(index)
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
        self.filtered_condensed_input_states = [
            list(v) for v in dict(self._input_states).items() if v[1]]
        self.filtered_condensed_output_states = [
            list(v) for v in dict(self._output_states).items() if v[1]]

    def __repr__(self):
        return f"{self.__class__} object with input '{self.input()}' and output '{self.output()}'"

    def __call__(self):
        return self.indices

    def __add__(self, other):
        return Indices(self.indices + other.indices)

    def __iadd__(self, other):
        return Indices(self.indices + other.indices)

    def __iter__(self):
        return iter(self.indices)

    def reduced(self):
        ''' Find how many indices it takes before input and output both move forward by one phone
        '''
        filtered = self.filter_empty_values()
        reduced = []
        intermediate_index = {
            'in': filtered[0][0], 'out': filtered[0][1]}
        for io in filtered:
            inp = io[0]
            outp = io[1]
            if inp == intermediate_index['in'] and outp > intermediate_index['out']:
                intermediate_index['out'] = outp
            if inp > intermediate_index['in'] and outp == intermediate_index['out']:
                intermediate_index['in'] = inp
            if inp > intermediate_index['in'] and outp > intermediate_index['out']:
                intermediate_index = {'in': inp, 'out': outp}
                reduced.append(copy.deepcopy(intermediate_index))
        reduced.append({"in": len(self.filtered_condensed_input_states),
                        "out": len(self.filtered_condensed_output_states)})
        reduced = [(x['in'], x['out']) for x in reduced]
        return reduced

    def filter_empty_values(self):
        filtered = []
        input_offset = 0
        output_offset = 0
        indices = self.indices
        for io in indices:
            if not io[0][1]:
                # epenthesis offsets the input by -1
                input_offset -= 1
            elif not io[1][1]:
                 # deletion offsets the output by -1
                output_offset -= 1
            else:
                filtered.append((io[0][0] + input_offset, io[1][0] + output_offset))
        return filtered

    def input(self):
        """ Return the input of a given transduction
        """
        return ''.join([state[1] for state in self.condensed_input_states])

    def output(self):
        """ Return the output of a given transduction
        """
        return ''.join([state[1] for state in self.condensed_output_states])


class IndexSequence():
    '''Class containing a sequence of IO States
    '''

    def __init__(self, *args: Indices):
        self.states = []
        for arg in args:
            if isinstance(arg, Indices):
                self.states.append(arg)
            if isinstance(arg, IndexSequence):
                self.states += self.unpack_states(arg)

    def __iter__(self):
        return iter(self.states)

    def __repr__(self):
        return f"{self.__class__} object with input '{self.input()}' and output '{self.output()}'"

    def unpack_states(self, seq):
        states = []
        for state in seq.states:
            if isinstance(state, Indices):
                states.append(state)
            if isinstance(state, Iterable) and any([isinstance(x, Indices) for x in state]):
                states += self.unpack_states(state)
        return states

    def compose_filtered_and_reduced_indices(self, i1, i2):
        if not i1:
            return i2
        i2_dict = dict(i2)
        i2_idx = 0
        results = []
        for i1_in, i1_out in i1:
            highest_i2_found = 0 if not results else results[-1][1]
            while i2_idx <= i1_out:
                if i2_idx in i2_dict and i2_dict[i2_idx] > highest_i2_found:
                    highest_i2_found = i2_dict[i2_idx]
                i2_idx += 1
            if results:
                assert(i1_in >= results[-1][0])
                assert(highest_i2_found >= results[-1][1])
            results.append((i1_in, highest_i2_found))
        return results

    def input(self):
        return self.states[0].input()

    def output(self):
        return self.states[-1].output()

    def reduced(self):
        ''' This is a reduced tuple-based format for indices. It requires that Indices in the
        IndexSequence be composed, and then they can be reduced to a list of tuples where each
        tuple contains an input and output index corresponding with that character. The list is equal
        to the length of unique characters
        '''
        composed_states = self.compose_filtered_and_reduced_indices(self.states[0].reduced(), self.states[1].reduced())
        counter = 2
        while counter < len(self.states):
            composed_states = self.compose_filtered_and_reduced_indices(
                composed_states, self.states[counter].reduced())
            counter += 1
        return composed_states
