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
    """This is the object returned after performing a transduction using a Transducer.

    Each TransductionGraph must be initialized with an input string.
    """

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
        """str: The input string that initialized the TransductionGraph."""
        return self._input_string

    @input_string.setter
    def input_string(self, value):
        raise ValueError(
            f'Sorry, you tried to change the input string to {value} but it cannot be changed')

    @property
    def output_string(self):
        """str: The output string."""
        return self._output_string

    @output_string.setter
    def output_string(self, value):
        self._output_string = value
        self._output_nodes = [[i, x] for i, x in enumerate(value)]

    @property
    def input_nodes(self):
        """List[List[int, str]]: A list of nodes (index and character string) corresponding to the input"""
        return self._input_nodes

    @input_nodes.setter
    def input_nodes(self, value):
        raise ValueError(
            f'Sorry, you tried to change the input nodes to {value} but they cannot be changed.')

    @property
    def output_nodes(self):
        """List[List[int, str]]: A list of nodes (index and character string) corresponding to the output"""
        return self._output_nodes

    @output_nodes.setter
    def output_nodes(self, value):
        raise ValueError(
            f'Sorry, you tried to change the output nodes to {value} but they cannot be changed directly. Change output_string instead.')

    @property
    def edges(self):
        """List[List[int, int]]: A list of edges (input node index, output node index) corresponding to the indices of the transformation"""
        return self._edges

    @edges.setter
    def edges(self, value):
        self._edges = value

    @property
    def debugger(self):
        """List[dict]: A list of rules applied during the transformation. Useful for debugging."""
        return self._debugger

    @debugger.setter
    def debugger(self, value):
        self._debugger = value

    @property
    def tiers(self):
        """List[TransductionGraph]: A list of TransductionGraph objects for each tier in the graph"""
        return self

    @tiers.setter
    def tiers(self, value):
        raise ValueError(
            f'Sorry, you tried to change the tiers to {value} but they cannot be changed')

    def pretty_edges(self):
        edges = copy.deepcopy(self._edges)
        edges.sort(key=lambda x: x[0])
        for i, edge in enumerate(edges):
            if edge[1] != None:
                edges[i] = [self._input_nodes[edge[0]]
                            [1], self._output_nodes[edge[1]][1]]
            else:
                edges[i] = [self._input_nodes[edge[0]][1], None]
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
        return f"{self.__class__} between {self.mapping.kwargs.get('in_lang', 'und')} and {self.mapping.kwargs.get('out_lang', 'und')}"

    def __call__(self, to_convert: str, index: bool = False, debugger: bool = False):
        """The basic method to transduce an input. A proxy for self.apply_rules.

        Args:
            to_convert (str): The string to convert.

        Returns:
            TransductionGraph: Returns an object with all the nodes representing input and output characters and their corresponding edges representing the indices of the transformation.
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

    def resolve_intermediate_chars(self, output_string):
        ''' Go through all chars and resolve any intermediate characters from the Private Supplementary Use Area
            to their mapped equivalents.
        '''
        indices_seen = defaultdict(int)
        for i, char in enumerate(output_string):
            intermediate_index = self._pua_to_index(char)
            # if not Private Supplementary Use character
            if intermediate_index < 0:
                continue
            else:
                output_char_index = indices_seen[intermediate_index]
                try:
                    output_string = output_string[:i] + \
                        self.mapping[intermediate_index]['out'][output_char_index] + \
                        output_string[i+1:]
                except IndexError:
                    indices_seen[intermediate_index] = 0
                    output_char_index = 0
                    output_string = output_string[:i] + \
                        self.mapping[intermediate_index]['out'][output_char_index] + \
                        output_string[i+1:]
                indices_seen[intermediate_index] += 1
        return output_string

    def update_explicit_indices(self, tg, match, io, intermediate_diff, out_string):
        """ Takes an arbitrary number of input & output strings and their corresponding index offsets.
            It then zips them up according to the provided indexing notation.

            Example:
                A rule that turns a sequence of k\u0313 to 'k might would have a default indexing of k -> ' and \u0313 -> k
                It might be desired though to show that k -> k and \u0313 -> ' and their indices were transposed.
                For this, the Mapping could be given the following: [{'in': 'k{1}\u0313{2}', 'out': "'{2}k{1}"}]
                Indices are found with r'(?<={)\d+(?=})' and characters are found with r'[^0-9\{\}]+(?={\d+})'
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
        deleted = 0
        for match_index, input_matches in inputs.items():
            try:
                output_matches = outputs[match_index]
            except KeyError:
                output_matches = []
            if len(input_matches) == len(output_matches):
                shortest = input_matches
                longest = output_matches
                process = 'basic'
            elif len(input_matches) < len(output_matches):
                shortest = input_matches
                longest = output_matches
                process = 'insert'
            else:
                shortest = output_matches
                longest = input_matches
                process = 'delete'
            for i, char in enumerate(longest):
                if process == 'basic' or i <= len(shortest) - 1:
                    input_index = input_matches[i]['index'] - intermediate_diff
                    output_index = output_matches[i]['index']
                    # don't allow insertion in basic process
                    if output_index >= len(match.group()) + start:
                        output_index = len(match.group()) + start - 1
                    tg.output_string = tg.output_string[:output_index] + \
                        char['string'] + tg.output_string[output_index+1:]
                    tg.edges = [x for x in tg.edges if x[1] != output_index]
                    tg.edges.append([input_index, output_index])
                else:
                    if process == 'insert':
                        input_index = input_matches[-1]['index'] - \
                            intermediate_diff
                        output_index = output_matches[i]['index']
                        tg.output_string = tg.output_string[:output_index] + \
                            char['string'] + tg.output_string[output_index:]
                        for i, edge in enumerate(tg.edges):
                            if edge[1] != None and edge[1] >= output_index:
                                tg.edges[i][1] += 1
                        tg.edges.append([input_index, output_index])
                    else:
                        input_index = input_matches[i]['index'] - \
                            intermediate_diff
                        if output_matches:
                            output_index = output_matches[-1]['index'] - deleted
                        else:
                            output_index = input_index + intermediate_diff - deleted
                        tg.output_string = tg.output_string[:output_index] + \
                            tg.output_string[output_index + 1:]
                        deleted += 1
                        if len(output_matches) > 0:
                            if [input_index, output_index] not in tg.edges:
                                tg.edges.append([input_index, output_index])
                            tg.edges = [
                                x for x in tg.edges if x[1] != output_index]
                        else:
                            for i, edge in enumerate(tg.edges):
                                if edge[1] != None and edge[1] == output_index:
                                    tg.edges[i][1] = None
                        for i, edge in enumerate(tg.edges):
                            if edge[1] != None and edge[1] > output_index:
                                tg.edges[i][1] -= 1

    def update_default_indices(self, tg, match, intermediate_diff, out_string):
        start = match.start() + intermediate_diff
        in_string = match.group()
        in_length = len(in_string)
        out_length = len(out_string)
        if in_length == out_length:
            for i, char in enumerate(out_string):
                tg.output_string = tg.output_string[:i +
                                                    start] + char + tg.output_string[i+start+1:]
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
        last_input_node = start
        last_output_node = start
        for i, char in enumerate(longest):
            # if the shorter string still has that output, keep that index
            if i <= len(shortest) - 1:
                tg.output_string = tg.output_string[:i+start] + \
                    out_string[i] + tg.output_string[i+start+1:]
                last_input_node = i + start
                last_output_node = i + start
            # otherwise...
            else:
                # add a new node and increment each following node
                # log the change in order to update the edges.
                if process == 'insert':
                    # Nodes
                    index_to_add = i + start
                    tg.output_string = tg.output_string[:index_to_add] + \
                        char + tg.output_string[index_to_add:]
                    # Edges
                    # Remove previously deleted and increment
                    for i, edge in enumerate(tg.edges):
                        if edge[1] != None and edge[1] >= index_to_add:
                            tg.edges[i][1] += 1
                    # add edge to index of last input character
                    last_input_node = max(
                        [x[0] for x in tg.edges if x[1] == last_output_node])
                    last_output_node = index_to_add
                    tg.edges.append([last_input_node, index_to_add])
                # delete the node and decrement each following node
                # log the change in order to update the edges.
                else:
                    # Nodes
                    index_to_delete = i + start - deleted
                    tg.output_string = tg.output_string[:index_to_delete] + \
                        tg.output_string[index_to_delete + 1:]
                    deleted += 1
                    # Edges
                    # delete
                    last_input_node = max(
                        [x[0] for x in tg.edges if x[1] == index_to_delete])
                    # if rule is not just a simple deletion,
                    # add an edge between the node and the last output node
                    if out_length > 0:
                        if [last_input_node, last_output_node] not in tg.edges:
                            tg.edges.append(
                                [last_input_node, last_output_node])
                        tg.edges = [x for x in tg.edges if x[1]
                                    != index_to_delete]
                    else:
                        for i, edge in enumerate(tg.edges):
                            if edge[1] != None and edge[1] == index_to_delete:
                                tg.edges[i][1] = None
                    # decrement
                    for i, edge in enumerate(tg.edges):
                        if edge[1] != None and edge[1] > index_to_delete:
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
                    self.update_default_indices(
                        tg, match, intermediate_diff, out_string)
                if io['in'] != io['out']:
                    tg.debugger.append({'input': debug_string,
                                        'output': tg.output_string,
                                        'rule': {k: v for k, v in io.items() if k != 'match_pattern'},
                                        'start': start,
                                        'end': end})
                out_string = re.sub(re.compile(r'{\d+}'), '', out_string)
                intermediate_diff += len(out_string) - len(match.group())
        if intermediate_forms:
            tg.output_string = self.resolve_intermediate_chars(
                tg.output_string)
        tg.edges = list(dict.fromkeys(
            [tuple(x) for x in sorted(tg.edges, key=lambda x: x[0])]))
        return tg


class CompositeTransductionGraph(TransductionGraph):
    """This is the object returned after performing a transduction using a CompositeTransducer.

    Each CompositeTransductionGraph must be initialized with a list of TransductionGraph objects.
    """

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
        """List[TransductionGraph]: A list of TransductionGraph objects for each tier in the CompositeTransducer"""
        return self._tiers

    @tiers.setter
    def tiers(self, value):
        raise ValueError(
            f'Sorry, you tried to change the tiers to {value} but they cannot be changed')

    def pretty_edges(self):
        pretty_edges = []
        for tier_i, edges in enumerate(self._edges):
            edges = copy.deepcopy(edges)
            edges.sort(key=lambda x: x[0])
            for i, edge in enumerate(edges):
                if edge[1] != None:
                    edges[i] = [self.tiers[tier_i].input_nodes[edge[0]]
                                [1], self.tiers[tier_i].output_nodes[edge[1]][1]]
                else:
                    edges[i] = [self.tiers[tier_i].input_nodes[edge[0]][1], None]
            pretty_edges.append(edges)
        return pretty_edges


class CompositeTransducer():
    """This class combines Transducer objects to form a CompositeTransducer object.

    Attributes:
        transducers (List[Transducer]): A list of Transducer objects to compose.
    """

    def __init__(self, transducers: List[Transducer]):
        self._transducers = transducers
        self._tiers = []

    def __repr__(self):
        return f"{self.__class__} between {self._transducers[0].mapping.kwargs.get('in_lang', 'und')} and {self._transducers[-1].mapping.kwargs.get('out_lang', 'und')}"

    def __call__(self, to_convert: str):
        return self.apply_rules(to_convert)

    def apply_rules(self, to_convert: str):
        for transducer in self._transducers:
            tg = transducer(to_convert)
            self._tiers.append(tg)
            to_convert = tg.output_string
        return CompositeTransductionGraph(self._tiers)
