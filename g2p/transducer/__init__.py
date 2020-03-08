# -*- coding: utf-8 -*-
"""
This module contains the Transducer and CompositeTransducer classes
which are responsible for performing transductions in the g2p library.
"""

import re
import copy
from typing import Dict, List, Pattern, Tuple, Union
from collections import defaultdict, OrderedDict
from collections.abc import Iterable
from g2p.mappings import Mapping
from g2p.mappings.utils import create_fixed_width_lookbehind, normalize
from g2p.exceptions import MalformedMapping
from g2p.log import LOGGER

# Avoid TypeError in Python < 3.7 (see
# https://stackoverflow.com/questions/6279305/typeerror-cannot-deepcopy-this-pattern-object)
copy._deepcopy_dispatch[type(re.compile(''))] = lambda r, _: r

# An Index is typed as follows:
# {input_index: int, {'input_string': str, 'output': {output_index: int, str}}}
# Example:
# {0: {'input_string': 'h', 'output': {0: 'ʔ'}}}
Index = Dict

# A ChangeLog is a list of changes (List[int])
# The first item (int) in a change is the index of where the change occurs, and the second item (int) is the change offset
# Example:
# an insertion of length 1 at index 0 followed by a deletion of length one at index 2
# [[0,1],[2,-1]]
ChangeLog = List[List[int]]

class TransductionGraph():
    ''' This class is the resulting output of calling a Transducer. 
        It contains the input and output string, their character nodes, and the edges between those nodes.
    '''

    def __init__(self, input_string: str):
        # Plain strings
        self._input_string = input_string
        self._output_string = input_string
        # Nodes
        self._input_nodes = [[i, x] for i, x in enumerate(input_string)]
        self._output_nodes = [[i, x] for i, x in enumerate(input_string)]
        # Edges
        self._edges = [[i, i] for i, x in enumerate(input_string)]
        # Debugger
        self._debugger = []

    def __str__(self):
        return self._output_string

    @property
    def input_string(self):
        return self._input_string

    @input_string.setter
    def input_string(self, value):
        raise ValueError(
            f'Sorry, you tried to change the input string to {value} but it cannot be changed')

    @property
    def output_string(self):
        return self._output_string

    @output_string.setter
    def output_string(self, value):
        self._output_string = value

    @property
    def input_nodes(self):
        return self._input_nodes

    @input_nodes.setter
    def input_nodes(self, value):
        raise ValueError(
            f'Sorry, you tried to change the input nodes to {value} but they cannot be changed')

    @property
    def output_nodes(self):
        return self._output_nodes

    @output_nodes.setter
    def output_nodes(self, value):
        self._output_nodes = value

    @property
    def edges(self):
        return self._edges

    @edges.setter
    def edges(self, value):
        self._edges = value

    @property
    def debugger(self):
        return self._debugger

    @debugger.setter
    def debugger(self, value):
        self._debugger = value

    def pretty_edges(self):
        edges = copy.deepcopy(self._edges)
        edges.sort(key=lambda x: x[0])
        for i, edge in enumerate(edges):
            edges[i] = [self._input_nodes[edge[0]][1], self._output_nodes[edge[1]][1]]
        return edges


class Transducer():
    """This is the fundamental class for performing conversions in the g2p library.

    Each Transducer must be initialized with a Mapping object. The Transducer object can then be called to apply the rules from Mapping on a given input.

    Attributes:
        mapping (Mapping): Formatted input/output pairs using the g2p.mappings.Mapping class.

    """

    def __init__(self, mapping: Mapping):
        self.mapping = mapping
        self.case_sensitive = mapping.kwargs['case_sensitive']
        self.norm_form = mapping.kwargs.get('norm_form', 'none')
        self.out_delimiter = mapping.kwargs.get('out_delimiter', '')
        self._index_match_pattern = re.compile(r'(?<={)\d+(?=})')
        self._char_match_pattern = re.compile(r'[^0-9\{\}]+(?={\d+})', re.U)

    def __repr__(self):
        return f"{__class__} between {self.mapping.kwargs.get('in_lang', 'und')} and {self.mapping.kwargs.get('out_lang', 'und')}"

    def __call__(self, to_convert: str, index: bool = False, debugger: bool = False):
        """The basic method to transduce an input. A proxy for self.apply_rules.

        Args:
            to_convert (str): The string to convert.
            index (bool, optional): Return indices in output. Defaults to False.
            debugger (bool, optional): Return intermediary steps for debugging. Defaults to False.

        Returns:
            Union[str, Tuple[str, Index], Tuple[str, List[dict]], Tuple[str, Index, List[dict]]]:
                Either returns a plain string (index=False, debugger=False),
                               a tuple with the converted string and indices (index=True, debugger=False),
                               a tuple with the converted string and corresponding rules (index=False, debugger=True),
                               a tuple with the converted string, indices and rules (index=True, debugger=True)
        """
        return self.apply_rules(to_convert)

    @staticmethod
    def _pua_to_index(string: str) -> int:
        """Given a string using with characters in the Supllementary Private Use Area A Unicode block
           Produce the number corresponding to the offset from the beginning of the block.

        Args:
            string (str): The string to convert

        Returns:
            int: The offset from the beginning of the block.
        """
        if string:
            intermediate_ord = ord(string[0])
            return intermediate_ord - 983040
        else:
            return - 1

    def resolve_intermediate_chars(self, output_nodes):
        ''' Go through all nodes and resolve any intermediate characters from the Private Supplementary Use Area
            to their mapped equivalents.
        '''
        output_nodes = copy.deepcopy(output_nodes)
        indices_seen = defaultdict(int)
        for i, node in enumerate(output_nodes):
            intermediate_index = self._pua_to_index(node[1])
            # if not Private Supplementary Use character
            if intermediate_index < 0:
                continue
            else:
                output_char_index = indices_seen[intermediate_index]
                try:
                    output_nodes[i][1] = self.mapping[intermediate_index]['out'][output_char_index]
                except IndexError:
                    indices_seen[intermediate_index] = 0
                    output_char_index = 0
                    output_nodes[i][1] = self.mapping[intermediate_index]['out'][output_char_index]
                indices_seen[intermediate_index] += 1
        return output_nodes

    def update_explicit_indices(self, tg, match, io, intermediate_diff, out_string) -> Index:
        """ Takes an arbitrary number of input & output strings and their corresponding index offsets.
            It then zips them up according to the provided indexing notation.

            Example:
                A rule that turns a sequence of k\u0313 to 'k might would have a default indexing of k -> ' and \u0313 -> k
                It might be desired though to show that k -> k and \u0313 -> ' and their indices were transposed.
                For this, the Mapping could be given the following: [{'in': 'k{1}\u0313{2}', 'out': "'{2}k{1}"}]
                Indices are found with r'(?<={)\d+(?=})' and characters are found with r'[^0-9\{\}]+(?={\d+})'

        Args:


        Returns:

        """
        input_char_matches = [x.group()
                              for x in self._char_match_pattern.finditer(io['in'])]
        input_match_indices = [
            x.group() for x in self._index_match_pattern.finditer(io['in'])]
        inputs = {}
        index = 0
        start = match.start() + intermediate_diff
        for i, m in enumerate(input_match_indices):
            for j, char in enumerate(input_char_matches[i]):
                if m in inputs:
                    inputs[m].append({'index': index + start, 'string': char})
                else:
                    inputs[m] = [{'index': index + start, 'string': char}]
                index += 1
        output_char_matches = [
            x.group() for x in self._char_match_pattern.finditer(out_string)]
        output_match_indices = [
            x.group() for x in self._index_match_pattern.finditer(out_string)]
        outputs = {}
        index = 0
        for i, m in enumerate(output_match_indices):
            for j, char in enumerate(output_char_matches[i]):
                if m in outputs:
                    outputs[m].append({'index': index + start, 'string': char})
                else:
                    outputs[m] = [{'index': index + start, 'string': char}]
                index += 1
        out_string = re.sub(re.compile(r'{\d+}'), '', out_string)
        self.update_default_indices(tg, match, intermediate_diff, out_string)
        for match_index, input_matches in inputs.items():
            output_matches = outputs[match_index]
            if len(input_matches) > len(output_matches):
                longest = input_matches
            else:
                longest = output_matches
            for i, item in enumerate(longest):
                if len(output_matches) > len(input_matches) and i > len(input_matches) - 1:
                    in_char = input_matches[-1]['index']
                    out_char = output_matches[i]['index']
                elif len(output_matches) < len(input_matches) and i > len(output_matches) - 1:
                    in_char = input_matches[i]['index']
                    out_char = output_matches[-1]['index']
                else:
                    in_char = input_matches[i]['index']
                    out_char = output_matches[i]['index']
                if out_char > len(match.group()) - 1 + start:
                    # increment
                    tg.edges = [x for x in tg.edges if x[1] != out_char]
                    for i, edge in enumerate(tg.edges):
                        if edge[1] >= out_char:
                            tg.edges[i][1] += 1
                    # add edge to index of last input character
                    tg.edges.append([in_char, out_char])
                elif out_char == len(out_string) - 1 + start and out_char < len(match.group()) - 1 + start:
                    tg.edges = [x for x in tg.edges if x[1] != out_char]
                    for i, edge in enumerate(tg.edges):
                        if edge[1] > out_char:
                            tg.edges[i][1] -= 1
                else:
                    for i in range(0, len(tg.edges)):
                        try:
                            if tg.edges[i][1] == out_char:
                                # this might cause problems...
                                del tg.edges[i]
                        except IndexError:
                            break
                    tg.edges.append([in_char, out_char])

    def update_default_indices(self, tg, match, intermediate_diff, out_string):
        start = match.start() + intermediate_diff
        in_string = match.group()
        in_length = len(in_string)
        out_length = len(out_string)
        if in_length == out_length:
            for i, char in enumerate(out_string):
                tg.output_nodes[i + start][1] = char
                tg.output_string = ''.join([x[1] for x in tg.output_nodes])
            return
        # default insertion(s)
        elif in_length < out_length:
            longest = out_string
            shortest = in_string
            process = 'insert'
        # default deletion(s)
        else:
            longest = in_string
            shortest = out_string
            process = 'delete'
        # iterate the longest string
        deleted = 0
        for i, char in enumerate(longest):
            # if the shorter string still has that output, keep that index
            if i <= len(shortest) - 1:
                tg.output_nodes[i + start][1] = out_string[i]
                tg.output_string = ''.join([x[1] for x in tg.output_nodes])
            # otherwise...
            else:
                # add a new node and increment each following node
                # log the change in order to update the edges.
                if process == 'insert':
                    # Nodes
                    index_to_add = i + start
                    new_node = [index_to_add, char]
                    tg.output_nodes = tg.output_nodes[:index_to_add] + [
                        [x[0] + 1, x[1]] for x in tg.output_nodes[index_to_add:]]
                    tg.output_nodes.insert(index_to_add, new_node)
                    tg.output_string = ''.join([x[1] for x in tg.output_nodes])
                    # Edges
                    # increment
                    for i, edge in enumerate(tg.edges):
                        if edge[1] >= index_to_add:
                            tg.edges[i][1] += 1
                    # add edge to index of last input character
                    tg.edges.append([in_length - 1 + start, index_to_add])
                # delete the node and decrement each following node
                # log the change in order to update the edges.
                else:
                    # Nodes
                    index_to_delete = i + start - deleted
                    del tg.output_nodes[index_to_delete]
                    deleted += 1
                    tg.output_nodes = tg.output_nodes[:index_to_delete] + [
                        [x[0] - 1, x[1]] for x in tg.output_nodes[index_to_delete:]]
                    tg.output_string = ''.join([x[1] for x in tg.output_nodes])

                    # Edges
                    # delete
                    tg.edges = [x for x in tg.edges if x[1] != index_to_delete]
                    # decrement
                    for i, edge in enumerate(tg.edges):
                        if edge[1] > index_to_delete:
                            tg.edges[i][1] -= 1

    def apply_rules(self, to_convert: str):
        # perform any normalization
        if not self.case_sensitive:
            to_convert = to_convert.lower()
        if self.norm_form:
            to_convert = normalize(to_convert, self.norm_form)
        tg = TransductionGraph(to_convert)
        # initialize values
        intermediate_forms = False
        # iterate rules
        for io in self.mapping:
            # Do not allow empty rules
            if not io['in'] and not io['out']:
                continue
            io = copy.deepcopy(io)
            intermediate_diff = 0
            for match in io['match_pattern'].finditer(tg.output_string):
                debug_string = tg.output_string
                start = match.start() + intermediate_diff
                end = match.end() + intermediate_diff
                if 'intermediate_form' in io:
                    out_string = io['intermediate_form']
                    intermediate_forms = True
                else:
                    out_string = io['out']
                if self.out_delimiter:
                    # if not end segment, add delimiter
                    if not end >= len(tg.output_string):
                        out_string += self.out_delimiter
                if any(self._char_match_pattern.finditer(io['in'])) and any(self._char_match_pattern.finditer(out_string)):
                    self.update_explicit_indices(
                        tg, match, io, intermediate_diff, out_string)
                else:
                    self.update_default_indices(tg, match, intermediate_diff, out_string)
                if io['in'] != io['out']:
                    tg.debugger.append({'input': debug_string,
                                        'output': tg.output_string,
                                        'rule': {k: v for k, v in io.items() if k != 'match_pattern'},
                                        'start': start,
                                        'end': end})
                out_string = re.sub(re.compile(r'{\d+}'), '', out_string)
                intermediate_diff += len(out_string) - len(match.group())
        if intermediate_forms:
            tg.output_nodes = self.resolve_intermediate_chars(tg.output_nodes)
            tg.output_string = ''.join([x[1] for x in tg.output_nodes])
        tg.edges = list(dict.fromkeys(
            [tuple(x) for x in sorted(tg.edges, key=lambda x: x[0])]))
        return tg

class CompositeTransductionGraph(TransductionGraph):
    ''' This class is the resulting output of calling a Transducer. 
        It contains the input and output string, their character nodes, and the edges between those nodes.
    '''

    def __init__(self, tg_list):
        # Plain strings
        self._input_string = tg_list[0].input_string
        self._output_string = tg_list[-1].output_string
        # Nodes
        self._input_nodes = tg_list[0].input_nodes
        self._output_nodes = tg_list[-1].output_nodes
        # Edges
        self._edges = [x.edges for x in tg_list]
        # Debugger
        self._debugger = [x.debugger for x in tg_list]
        # Tiers
        self._tiers = tg_list

    @property
    def tiers(self):
        return self._tiers

    @tiers.setter
    def tiers(self, value):
        self._tiers = value

class CompositeTransducer():
    """This class combines Transducer objects to form a CompositeTransducer object.

    Attributes:
        transducers (List[Transducer]): A list of Transducer objects to compose.
    """

    def __init__(self, transducers: List[Transducer]):
        self._transducers = transducers
        self._tiers = []

    def __repr__(self):
        return f"{__class__} between {self._transducers[0].mapping.kwargs.get('in_lang', 'und')} and {self._transducers[-1].mapping.kwargs.get('out_lang', 'und')}"

    def __call__(self, to_convert: str):
        return self.apply_rules(to_convert)

    def apply_rules(self, to_convert: str):
        for transducer in self._transducers:
            tg = transducer(to_convert)
            self._tiers.append(tg)
            to_convert = tg.output_string
        return CompositeTransductionGraph(self._tiers)
