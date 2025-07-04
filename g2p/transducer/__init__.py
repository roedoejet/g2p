"""
This module contains the Transducer and CompositeTransducer classes
which are responsible for performing transductions in the g2p library.
"""

import copy
import re
import unicodedata
from collections import OrderedDict, defaultdict
from typing import DefaultDict, Dict, List, Optional, Set, Tuple, Union

import text_unidecode  # type: ignore

from g2p.log import LOGGER
from g2p.mappings import MAPPING_TYPE, Mapping
from g2p.mappings.langs.utils import is_arpabet, is_panphon
from g2p.mappings.utils import (
    Rule,
    compose_indices,
    find_alignment,
    is_ipa,
    normalize,
    normalize_with_indices,
    strip_index_notation,
    unicode_escape,
)
from g2p.shared_types import BaseTokenizer, BaseTransducer, BaseTransductionGraph

# Avoid TypeError in Python < 3.7 (see
# https://stackoverflow.com/questions/6279305/typeerror-cannot-deepcopy-this-pattern-object)
copy._deepcopy_dispatch[type(re.compile(""))] = lambda r, _: r  # type: ignore

# An Index is typed as follows:
# {input_index: int, {'input_string': str, 'output': {output_index: int, str}}}
# Example:
# {0: {'input_string': 'h', 'output': {0: 'ʔ'}}}
Index = Dict

# A ChangeLog is a list of changes (List[int])
# The first item (int) in a change is the index of where the change occurs, and
# the second item (int) is the change offset
# Example:
# an insertion of length 1 at index 0 followed by a deletion of length one at index 2
# [[0,1],[2,-1]]
ChangeLog = List[List[int]]

UNIDECODE_SPECIALS = ["@", "?", "'", ",", ":"]


def normalize_edges(
    edges: List[Tuple[int, Optional[int]]],
) -> List[Tuple[int, Optional[int]]]:
    """Normalize and sort a list of edges.

    Specifically, this:

    - Removes any non-deletion edges with the same input index as a deletion
    - Resolves all deletions to map the outputs to the previous index if possible,
      the following index if possible, or otherwise None (in practice this means
      that None only occurs if the output is empty)
    - Sorts edges based on the input and suppresses duplicates
    """
    to_remove: Set[int] = set()
    for i, edge in enumerate(edges):
        if edge[1] is None:
            for j, other_edge in enumerate(edges):
                if other_edge != edge and other_edge[0] == edge[0]:
                    to_remove.add(j)
    edges = [edge for i, edge in enumerate(edges) if i not in to_remove]
    # sort based on inputs
    edges.sort(key=lambda x: x[0])
    for i, edge in enumerate(edges):
        if edge[1] is None:
            # if previous exists, use that, otherwise use following, otherwise None
            previous = [x for x in edges[:i] if x[1] is not None]
            # Note: if len(edges) == 1, edges[1:] is empty, not an IndexError
            following = [x for x in edges[i + 1 :] if x[1] is not None]
            if previous:
                edges[i] = (edge[0], previous[-1][1])
            elif following:
                edges[i] = (edge[0], following[0][1])
    # uniquify preserving order
    return list(OrderedDict.fromkeys((i, j) for i, j in edges))


class TransductionGraph(BaseTransductionGraph):
    """This is the object returned after performing a transduction using a Transducer.

    Each TransductionGraph must be initialized with an input string.
    """

    def __init__(self, input_string: str):
        # Plain strings
        self._input_string = input_string
        self._output_string = input_string
        # Nodes
        self._input_nodes: List[Tuple[int, str]] = list(enumerate(input_string))
        self._output_nodes: List[Tuple[int, str]] = list(enumerate(input_string))
        # Edges
        self._edges: List[Tuple[int, Optional[int]]] = [
            (i, i) for i in range(len(input_string))
        ]
        # Debugger
        self._debugger = []  # type: ignore

    def __str__(self):
        return self._output_string

    @property
    def input_string(self) -> str:
        """The input string that initialized the TransductionGraph."""
        return self._input_string

    @input_string.setter
    def input_string(self, value):
        # Only modify this if you're also adjusting the edges at the same time!
        self._input_string = value
        self._input_nodes = list(enumerate(value))

    @property
    def output_string(self) -> str:
        """str: The output string."""
        return self._output_string

    @output_string.setter
    def output_string(self, value):
        self._output_string = value
        self._output_nodes = list(enumerate(value))

    @property
    def input_nodes(self) -> List[Tuple[int, str]]:
        """List of nodes (index and character string) corresponding to the input"""
        return self._input_nodes

    @input_nodes.setter
    def input_nodes(self, value):
        raise ValueError(
            f"Sorry, you tried to change the input nodes to {value} but they cannot be changed."
        )

    @property
    def output_nodes(self) -> List[Tuple[int, str]]:
        """List of nodes (index and character string) corresponding to the output"""
        return self._output_nodes

    @output_nodes.setter
    def output_nodes(self, value):
        raise ValueError(
            f"Sorry, you tried to change the output nodes to {value} but they cannot be changed directly. Change output_string instead."
        )

    @property
    def edges(self) -> List:
        """List[Tuple[int, Optional[int]]] of edges for the transformation.

        Note that currently this is *not* the same between
        TransductionGraph and CompositeTransductionGraph.
        """
        return self._edges

    @edges.setter
    def edges(self, value):
        self._edges = value

    @property
    def debugger(self) -> List[list]:
        """List[List[dict]]: A list of lists of rules applied during the
        transformation. Useful for debugging.

        Note that currently this is *not* the same between TransductionGraph
        and CompositeTransductionGraph.

        """
        return self._debugger

    @debugger.setter
    def debugger(self, value):
        self._debugger = value

    @property
    def tiers(self) -> List["TransductionGraph"]:  # noqa: F821
        """A list of TransductionGraph objects for each tier in the graph
        (there is one tier)."""
        return [self]

    @tiers.setter
    def tiers(self, value):
        raise ValueError(
            f"Sorry, you tried to change the tiers to {value} but they cannot be changed"
        )

    def pretty_edges(self):
        """List[Tuple[str, str]] of edges resolved to the string nodes.

        Note that this currently *not* the same output between
        TransductionGraph and ComposedTransductionGraph.
        """
        edges = self._edges[:]
        edges.sort(key=lambda x: x[0])
        out_edges = []
        for edge in edges:
            assert edge[0] is not None  # Empty inputs are not allowed
            if edge[1] is None:
                out_edges.append((self._input_nodes[edge[0]][1], None))
            else:
                out_edges.append(
                    (
                        self._input_nodes[edge[0]][1],
                        self._output_nodes[edge[1]][1],
                    )
                )
        return out_edges

    def alignments(self) -> List[Tuple[int, Optional[int]]]:
        """Alignments (input node index, output node index) for the full
        (possibly composed) transduction.

        Insertions are not allowed in rules, but deletions are.  In
        most cases they will *not* be represented as `None` in the
        output node index, except in the case where there is a
        deletion and the output string is empty.

        Nonetheless code must be robust to the possibility of `None`
        occurring as the output of an alignment.

        Note that this method *is* compatible between TransductionGraph
        and CompositeTransductionGraph.

        """
        return self._edges

    def substring_alignments(self) -> List[Tuple[str, str]]:  # noqa: C901
        """Alignments of input to output substrings for this graph.

        As opposed to `pretty_edges`, this method will return the
        one-to-many or many-to-one alignments produced by a
        conversion.  It is also the same between TransductionGraph and
        CompositeTransductionGraph.  For example, assuming this input
        and output with these edges::

            ABCDEFF
            aabbcdef
            [(0, 0), (0, 1), (1, 2), (1, 3), (2, 4), (3, 5),
             (4, 6), (5, 7), (6, 7)]

        it should return::

            [('A', 'aa'), ('B', 'bb'), ('C', c'), ('D', 'd'),
             ('E', 'e'), ('FF', 'f')]

        In the case of reorderings, the substrings returned correspond
        to the minimal *monotonic* alignments, that is, the minimal
        subsequences which preserve ordering between the input and
        output.  So, for example given these edges::

            ABCDEF
            abefcd
            [(0, 0), (1, 1), (2, 4), (3, 5), (4, 2), (5, 3)]

        it should return::

            [('A', 'a'), ('B', 'b'), ('CDEF', 'efcd')]

        This means, that in the case of truly radical reorderings,
        there is no "alignment" per se.  This is highly unlikely to
        occur, given the constrained nature of g2p rules.

        Note that in the case of multi-character outputs such as in
        ARPABET, the output substrings *do not necessarily* correspond
        to tokens, and spaces are treated as any other character in
        the alignment (thus, alignments of (' ', ' ') are possible).
        If you wish to reconstruct the input it is your resonsibility
        to collect all the alignments corresponding to an output token
        (this should not be too hard to do).

        """
        alignments = self.alignments()

        def find_monotonic_segments(alignments):
            segments = []
            # Sort according to input and output (None is not allowed on input)
            isort = sorted(
                alignments, key=lambda x: (x[0], x[0]) if x[1] is None else x
            )
            osort = sorted(
                alignments, key=lambda x: (x[0], x[0]) if x[1] is None else (x[1], x[0])
            )
            # print("isort:", isort)
            # print("osort:", osort)
            # Use -1 as flag value because None has a meaning in alignments
            istart = ostart = iend = oend = -1
            for iedge, oedge in zip(isort, osort):
                # Create a new segment if the sorting orders agree, or
                # if the subsequent alignments cannot overlap with the
                # current segment
                non_overlapping = (
                    -1 not in (iend, oend) and iedge[0] > iend and oedge[0] > oend
                )
                if iedge == oedge or non_overlapping:
                    # Output an existing segment if we have one
                    if iend != -1:
                        segments.append((istart, iend, ostart, oend))
                        istart = ostart = iend = oend = -1
                    # And if we have entered an agreement region output that
                    if iedge == oedge:
                        ipos, opos = iedge
                        segments.append((ipos, ipos, opos, opos))
                        istart = ostart = iend = oend = -1
                        continue
                if istart == -1:  # Start a new segment
                    # Smallest input index (by definition)
                    istart = iedge[0]
                    # Smallest output index (by definition)
                    ostart = oedge[1]
                    # These are updated below
                    iend = oedge[0]
                    oend = iedge[1]
                else:  # Expand an existing segment
                    assert oedge[0] is not None
                    assert iedge[1] is not None
                    iend = max(iend, oedge[0])
                    # Replace None with not-None
                    if oend is None:
                        oend = iedge[1]
                    elif iedge[1] is not None:
                        oend = max(oend, iedge[1])
            if istart != -1:
                assert iend != -1
            # Output a final segment if one exists
            if iend != -1:
                segments.append((istart, iend, ostart, oend))
            return segments

        # Construct areas of agreement
        segments = find_monotonic_segments(alignments)
        # print("segments:", segments)

        def merge_overlapping_segments(segments):
            if len(segments) <= 1:
                return segments
            istart, iend, ostart, oend = segments[0]
            output = []
            for seg in segments[1:]:
                # If *start* points are outside current segment, start a new one
                if None in (seg[2], oend):  # handle only None in outputs
                    output_outside = not (None, None) == (seg[2], oend)
                else:
                    output_outside = seg[2] > oend
                if seg[0] > iend and output_outside:
                    output.append((istart, iend, ostart, oend))
                    istart, iend, ostart, oend = seg
                else:
                    # Update endpoints to include this segment
                    iend = seg[1]
                    oend = seg[3]
            output.append((istart, iend, ostart, oend))
            return output

        # Merge overlapping segments
        segments = merge_overlapping_segments(segments)
        # print("merged:", segments)
        # Output string alignments
        substrings = []
        for istart, iend, ostart, oend in segments:
            istr = self._input_string[istart : iend + 1]
            if ostart is None:
                assert oend is None
                ostr = ""
            else:
                ostr = self._output_string[ostart : oend + 1]
            substrings.append((istr, ostr))
        return substrings

    def as_dict(self) -> dict:
        return {
            "edges": self._edges,
            "input": self._input_string,
            "output": self._output_string,
            "input_nodes": self._input_nodes,
            "output_nodes": self._output_nodes,
        }

    def clear_debugger(self):
        self._debugger = []

    def append(self, tg):
        """Append the nodes, edges, strings and debugger from tg to self,
        shifting indices so tg nodes and edges are added after those of self.
        """
        in_offset = len(self._input_nodes)
        out_offset = len(self._output_nodes)
        # append input and output strings
        self._input_string += tg._input_string
        self._output_string += tg._output_string
        # append nodes
        self._input_nodes += [(i + in_offset, x) for (i, x) in tg._input_nodes]
        self._output_nodes += [(i + out_offset, x) for (i, x) in tg._output_nodes]
        # append edges and normalize
        self._edges = normalize_edges(
            self._edges
            + [
                (i + in_offset, None if j is None else j + out_offset)
                for i, j in tg.edges
            ]
        )
        # append debuggers
        self._debugger += tg._debugger

    def __iadd__(self, tg):
        self.append(tg)
        return self


class Transducer(BaseTransducer):
    """This is the fundamental class for performing conversions in the g2p library.

    Each Transducer must be initialized with a Mapping object. The Transducer
    object can then be called to apply the rules from Mapping on a given input.

    Attributes:
        mapping (Mapping): Formatted input/output pairs using the g2p.mappings.Mapping class.
    """

    def __init__(self, mapping: Mapping):
        self.mapping = mapping
        self.case_sensitive = mapping.case_sensitive
        self.preserve_case = mapping.preserve_case
        self.norm_form = mapping.norm_form
        self.out_delimiter = mapping.out_delimiter
        self._index_match_pattern = re.compile(r"(?<={)\d+(?=})")
        self._char_match_pattern = re.compile(r"[^0-9\{\}]+(?={\d+})", re.U)

    def __repr__(self):
        return f"{self.__class__} between {self.mapping.in_lang} and {self.mapping.out_lang}"

    def __call__(self, to_convert: str):
        """The basic method to transduce an input. A proxy for self.apply_rules.

        Args:
            to_convert (str): The string to convert.

        Returns:
            TransductionGraph: Returns an object with all the nodes representing input
            and output characters and their corresponding edges representing the indices
            of the transformation.
        """
        tg = self.apply_rules(to_convert)
        if self.preserve_case:
            return preserve_case(tg, self.mapping.case_equivalencies)
        else:
            return tg

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
            return -1

    @property
    def in_lang(self) -> str:
        """Input language node name"""
        return self.mapping.in_lang

    @property
    def out_lang(self) -> str:
        """Output language node name"""
        return self.mapping.out_lang

    @property
    def transducers(self) -> List["Transducer"]:  # noqa: F821
        """Sequence of underlying Transducer objects"""
        return [self]

    def resolve_intermediate_chars(self, output_string) -> str:
        """Go through all chars and resolve any intermediate characters from the Private Supplementary Use Area
        to their mapped equivalents.
        """

        indices_seen: Dict[int, int] = defaultdict(int)
        for i, char in enumerate(output_string):
            intermediate_index = self._pua_to_index(char)
            # if not Private Supplementary Use character
            if intermediate_index < 0:
                continue
            output_char_index = indices_seen[intermediate_index]
            try:
                output_string = (
                    output_string[:i]
                    + strip_index_notation(
                        self.mapping.rules[intermediate_index].rule_output
                    )[output_char_index]
                    + output_string[i + 1 :]
                )
            except IndexError:
                indices_seen[intermediate_index] = 0
                output_char_index = 0
                output_string = (
                    output_string[:i]
                    + strip_index_notation(
                        self.mapping.rules[intermediate_index].rule_output
                    )[output_char_index]
                    + output_string[i + 1 :]
                )
            indices_seen[intermediate_index] += 1
        return output_string

    def get_match_groups(
        self,
        tg: TransductionGraph,
        start_end: Tuple[int, int],
        io: Rule,
        diff_from_input: DefaultDict,
        out_string: str,
        output_start: int,
    ) -> Tuple[dict, dict]:
        """Take the inputs to explicit indices matching and create groups of
            Input and Output matches that are grouped by their explicit indices.

            For example, applying a rule that is defined: a{1}b{2} → b{2}a{1} on the input "ab"
            will return inputs, outputs where:

            inputs = {'1': [{'index': 0, 'string': 'a'}], '2': [{'index': 1, 'string': 'b'}] }
            outputs = {'1': [{'index': 0, 'string': 'b'}], '2': [{'index': 1, 'string': 'a'}] }

            This allows input match groups to be iterated through in sequence regardless of their
            character sequence.

        Args:
            tg (TransductionGraph): the graph holding information about the transduction
            start_end (Tuple(int, int)): a tuple containing the start and end of the input match
            io (Rule): an input/output rule
            diff_from_input (DefaultDict): A dictionary containing the single character distance
                                           from a given character index to its input
            out_string (str): the raw output string
            output_start (int): the diff-offset start of the match with respect to the output

        Returns:
            inputs (dict): dictionary containing matches grouped by explicit index match
            outputs (dict): dictionary containing matches grouped by explicit index match
        """
        input_char_matches = [
            x.group() for x in self._char_match_pattern.finditer(io.rule_input)
        ]
        input_match_indices = [
            x.group() for x in self._index_match_pattern.finditer(io.rule_input)
        ]
        inputs: Dict[str, List[dict]] = {}
        index = 0

        input_start = (
            start_end[0] - diff_from_input[self.get_input_from_output(tg, start_end[0])]
        )

        for i, m in enumerate(input_match_indices):
            for char in input_char_matches[i]:
                if m in inputs:
                    inputs[m].append({"index": index + input_start, "string": char})
                else:
                    inputs[m] = [{"index": index + input_start, "string": char}]
                index += 1
        output_char_matches = [
            x.group() for x in self._char_match_pattern.finditer(out_string)
        ]
        output_match_indices = [
            x.group() for x in self._index_match_pattern.finditer(out_string)
        ]
        outputs: Dict[str, List[dict]] = {}
        index = 0
        for i, m in enumerate(output_match_indices):
            for char in output_char_matches[i]:
                if m in outputs:
                    outputs[m].append({"index": index + output_start, "string": char})
                else:
                    outputs[m] = [{"index": index + output_start, "string": char}]
                index += 1
        return inputs, outputs

    def delete_character(self, tg, index_to_delete, ahh):
        """Delete character at `index_to_delete` in TransductionGraph output

        Args:
            tg (TransductionGraph): the current Transduction Graph
            index_to_delete (int): index of character to delete
            ahh (int): current value of i in calling loop
        """
        # delete character
        tg.output_string = (
            tg.output_string[:index_to_delete] + tg.output_string[index_to_delete + 1 :]
        )
        # update indices
        for k, edge in enumerate(tg.edges):
            if (
                edge[1] is not None
                and (ahh == 0 or tg.edges[k - 1][1] is None)
                and edge[1] == index_to_delete
            ):
                tg.edges[k] = (edge[0], None)
            elif edge[1] is not None and edge[1] >= index_to_delete:
                tg.edges[k] = (edge[0], edge[1] - 1)

    def insert_character(self, tg, character_to_insert, index_to_insert_character):
        """Insert character at `index_to_insert_character` in TransductionGraph output

        Args:
            tg (TransductionGraph): the current Transduction Graph
            character_to_insert (str): the character to insert
            index_to_insert_character (int): index of character to insert
        """
        assert len(character_to_insert) == 1
        tg.output_string = (
            tg.output_string[:index_to_insert_character]
            + character_to_insert
            + tg.output_string[index_to_insert_character:]
        )
        for j, edge in enumerate(tg.edges):
            if edge[1] is not None and edge[1] >= index_to_insert_character:
                tg.edges[j] = (edge[0], edge[1] + 1)

    def change_character(self, tg, character, index_to_change):
        """Change character at `index_to_change` in TransductionGraph output to `character`

        Args:
            tg (TransductionGraph): the current Transduction Graph
            character (str): the character to change to
            index_to_change (int): index of character to change
        """
        assert len(character) == 1
        tg.output_string = (
            tg.output_string[:index_to_change]
            + character
            + tg.output_string[index_to_change + 1 :]
        )

    def update_explicit_indices(
        self, tg, match, start_end, io, diff_from_input, diff_from_output, out_string
    ):
        r"""Takes an arbitrary number of input & output strings and their corresponding index offsets.
        It then zips them up according to the provided indexing notation.

        Example:
            A rule that turns a sequence of k\u0313 to 'k might would have a default indexing of k -> ' and \u0313 -> k
            It might be desired though to show that k -> k and \u0313 -> ' and their indices were transposed.
            For this, the Mapping could be given the following: [{'in': 'k{1}\u0313{2}', 'out': "'{2}k{1}"}]
            Indices are found with r'(?<={)\d+(?=})' and characters are found with r'[^0-9\{\}]+(?={\d+})'
        """
        output_start = start_end[0] - diff_from_output[start_end[0]]
        inputs, outputs = self.get_match_groups(
            tg, start_end, io, diff_from_input, out_string, output_start
        )
        out_string = strip_index_notation(out_string)
        # keep track of deletions that haven't yet been processed by diff_from_x
        deleted = 0
        for match_index, input_matches in inputs.items():
            try:
                output_matches = outputs[match_index]
            except KeyError:
                output_matches = []
            process, longest, shortest = self.get_longest_and_shortest(
                input_matches, output_matches
            )
            for i, char in enumerate(longest):
                # deleted segments don't have indices
                if process != "delete" or i <= len(shortest) - 1:
                    output_index = (
                        output_matches[i]["index"]
                        + diff_from_output[output_matches[i]["index"]]
                    )
                # do basic transduction
                if i <= len(shortest) - 1:
                    if output_index >= len(match.group()) + output_start:
                        output_index = len(match.group()) + output_start - 1
                    self.change_character(tg, output_matches[i]["string"], output_index)
                    # this is needed for metathesis,
                    # but metathesis is only expressable by using explicit indices,
                    # so we fix these indices outside of the change_character method
                    tg.edges = [x for x in tg.edges if x[1] != output_index]
                    tg.edges.append([input_matches[i]["index"], output_index])
                elif process == "insert":
                    self.insert_character(tg, char["string"], output_index)
                    # then add insertion edge
                    tg.edges.append([input_matches[-1]["index"], output_index])
                elif process == "delete":
                    if output_matches:
                        index_to_delete = output_matches[-1]["index"] + i - deleted
                    # if there is no output_matches
                    else:
                        index_to_delete = (
                            input_matches[i]["index"]
                            + diff_from_output[input_matches[i]["index"]]
                            - deleted
                        )
                    self.delete_character(tg, index_to_delete, i)
                    deleted += 1
                    if output_matches:
                        tg.edges = [x for x in tg.edges if x[1] != index_to_delete]
                        tg.edges.append([input_matches[i]["index"], None])

    def get_input_from_output(self, tg, output_node):
        return max(x[0] for x in tg.edges if x[1] == output_node)

    def get_longest_and_shortest(
        self, in_string_or_matches, out_string_or_matches
    ) -> Tuple[str, Union[str, list], Union[str, list]]:
        """Given two strings or match lists determine the longest and shortest. If
           the input is longer than the output, the process is to delete,
           if the output is longer than the input, the process is to insert.
           If the input and output are the same length, the process is basic.

        Args:
            in_string_or_matches (str|List): input string
            out_string_or_matches (str|List): output string
        """
        in_length = len(in_string_or_matches)
        out_length = len(out_string_or_matches)
        if in_length > out_length:
            return "delete", in_string_or_matches, out_string_or_matches
        elif in_length < out_length:
            return "insert", out_string_or_matches, in_string_or_matches
        else:
            return "basic", out_string_or_matches, in_string_or_matches

    def update_default_indices(
        self,
        tg,
        match_start,
        diff_from_output,
        in_string,
        out_string,
    ):
        process, longest, shortest = self.get_longest_and_shortest(
            in_string, out_string
        )

        deleted = 0
        for i, char in enumerate(longest):
            output_index = i + match_start + diff_from_output[i + match_start]
            # if the shorter string still has that output:
            #   keep that index, and convert the character
            if i <= len(shortest) - 1:
                self.change_character(tg, out_string[i], output_index)
            # if the output string is longer than the input string
            # then it is an insertion and we should:
            #  - increment every edge after the insertion
            #  - connect every input edge connected to the previous output to that new insertion
            elif process == "insert":
                self.insert_character(tg, char, output_index)
                # add insertion edge
                for edge in tg.edges:
                    if edge[1] == output_index - 1:
                        tg.edges.append([edge[0], output_index])
            # if the input string is longer than the output string
            # then it is a deletion and we should:
            #  - turn the edge to the deleted index to None if there are no non-None preceding characters
            #  - decrement edges following the deleted character
            elif process == "delete":
                # Nodes
                index_to_delete = output_index - deleted
                self.delete_character(tg, index_to_delete, i)
                deleted += 1

    def apply_unidecode(self, to_convert: str) -> TransductionGraph:
        to_convert = unicode_escape(to_convert)
        saved_to_convert = to_convert
        if self.norm_form:
            to_convert, norm_indices = normalize_with_indices(
                to_convert, self.norm_form
            )
        else:
            norm_indices = None
        tg = TransductionGraph(to_convert)

        # Conversion is done character by character using unidecode
        # We retain spaces in the input, but spaces from unidecode are removed
        converted = []
        for rule_input in to_convert:
            unidecode_str = text_unidecode.unidecode(
                unicodedata.normalize("NFKC", rule_input)
            )
            cc = [
                c
                for c in unidecode_str
                if c.isalpha() or c in UNIDECODE_SPECIALS or rule_input.isspace()
            ]
            converted.append("".join(cc))
        tg.output_string = "".join(converted)

        # Edges are calculated to follow the conversion step by step
        if not tg.output_string:
            # Some inputs get completely deleted by unidecode, in which case there are no
            # valid edges to output.
            tg.edges = []
        else:
            edges = []
            x_len, y_len = 0, 0
            for tgt in converted:
                if tgt:
                    for _ in tgt:
                        edges.append((x_len, y_len))
                        y_len += 1
                else:
                    edges.append((x_len, max(y_len - 1, 0)))
                x_len += 1
            if norm_indices:
                tg.edges = compose_indices(norm_indices, edges)
                tg.input_string = saved_to_convert
            else:
                tg.edges = edges

        return tg

    def apply_lexicon(self, to_convert: str):
        tg = TransductionGraph(to_convert)
        if not self.case_sensitive:
            to_convert = to_convert.lower()
        alignment = find_alignment(self.mapping.alignments, to_convert)
        if not alignment:
            tg.edges = []
            tg.output_string = ""
        else:
            tg.output_string = ""
            edges: List[Tuple[int, int]] = []
            in_pos = 0
            out_pos = 0
            for n_inputs, outtxt in alignment:
                for i in range(n_inputs):
                    for j in range(len(outtxt)):
                        edges.append((in_pos + i, out_pos + j))
                    if len(outtxt) == 0:
                        # Attach deletions to the previous output if
                        # possible, otherwise the next output.  This
                        # will be modified to None below if the output
                        # string is empty.
                        edges.append((in_pos + i, max(0, out_pos - 1)))
                if n_inputs == 0:
                    # Attach insertions to the previous input
                    for j in range(len(outtxt)):
                        edges.append((in_pos, out_pos + j))
                in_pos += n_inputs
                if len(outtxt) != 0:
                    out_pos += len(outtxt) + len(self.out_delimiter)
                    # Be bug-compatible with mappings and add an extra delimiter
                    tg.output_string += outtxt + self.out_delimiter
            # Fix up bogus indices here
            out_len = len(tg.output_string)
            tg.edges = []
            for in_pos, out_pos in edges:
                assert in_pos is not None
                if out_pos >= out_len:
                    tg.edges.append((in_pos, None if out_len == 0 else out_len - 1))
                else:
                    tg.edges.append((in_pos, out_pos))
        return tg

    def apply_rules(self, to_convert: str):  # noqa: C901
        if self.mapping.type == MAPPING_TYPE.unidecode:
            return self.apply_unidecode(to_convert)
        elif self.mapping.type == MAPPING_TYPE.lexicon:
            return self.apply_lexicon(to_convert)
        # perform any normalization
        to_convert = unicode_escape(to_convert)
        saved_to_convert = to_convert
        if not self.case_sensitive:
            to_convert = to_convert.lower()
        if self.norm_form:
            to_convert, norm_indices = normalize_with_indices(
                to_convert, self.norm_form
            )
        else:
            norm_indices = None
        tg = TransductionGraph(to_convert)
        tg.debugger.append([])

        # initialize values
        intermediate_forms = False
        # iterate rules
        # these variables tracks changes in the output string across processing
        # matches of the same pattern
        diff_from_input = defaultdict(int, {n: 0 for n in range(len(tg.output_string))})
        for io in self.mapping.rules:
            assert isinstance(io, Rule)
            # Do not allow empty rules
            if not io.rule_input and not io.rule_output:
                continue
            io = copy.deepcopy(io)
            # create empty out_string
            out_string = ""
            diff_from_output = defaultdict(
                int, {n: 0 for n in range(len(tg.output_string))}
            )

            matches = reversed(list(io.match_pattern.finditer(tg.output_string)))  # type: ignore
            for match_i, match in enumerate(matches):
                debug_string = tg.output_string
                start = match.start()
                end = match.end()
                if match_i:
                    start += diff_from_output[start]
                    end += diff_from_output[end - 1]
                if io.intermediate_form:
                    out_string = io.intermediate_form
                    intermediate_forms = True
                else:
                    out_string = io.rule_output
                if self.out_delimiter:
                    out_string += self.out_delimiter
                if any(self._char_match_pattern.finditer(io.rule_input)) and any(
                    self._char_match_pattern.finditer(out_string)
                ):
                    self.update_explicit_indices(
                        tg,
                        match,
                        (start, end),
                        io,
                        diff_from_input,
                        diff_from_output,
                        out_string,
                    )
                else:
                    self.update_default_indices(
                        tg,
                        match.start(),
                        diff_from_output,
                        match.group(),
                        out_string,
                    )
                if (
                    io.rule_input != io.rule_output
                    or io.context_after
                    or io.context_before
                ):
                    tg.debugger[-1].append(
                        {
                            "input": debug_string,
                            "output": tg.output_string,
                            "rule": io.export_to_dict(),
                            "start": match.start(),
                            "end": match.end(),
                        }
                    )
                out_string = strip_index_notation(out_string)
                # update the output intermediate diff after each match
                diff = len(out_string) - len(match.group())

                try:
                    input_index = self.get_input_from_output(tg, match.end() - 1)
                except ValueError:
                    # it's been deleted
                    input_index = match.end() - 1
                for n in range(
                    match.end() - 1 + diff,
                    max(len(diff_from_output) + diff, len(diff_from_output)),
                ):
                    diff_from_output[n] += diff
                for n in range(input_index, len(diff_from_input)):
                    diff_from_input[n] += diff

        if intermediate_forms:
            tg.output_string = self.resolve_intermediate_chars(tg.output_string)

        # sort and fix None
        tg.edges = normalize_edges(tg.edges)
        if norm_indices is not None:
            tg.edges = compose_indices(norm_indices, tg.edges)
            tg.input_string = saved_to_convert
        return tg

    def check(
        self,
        tg: TransductionGraph,
        shallow=False,
        display_warnings=False,
        original_input=None,
    ) -> bool:
        out_lang = self.mapping.out_lang
        if "eng-arpabet" in out_lang:
            if is_arpabet(tg.output_string):
                return True
            if display_warnings:
                display_input = original_input or tg.input_string
                LOGGER.warning(
                    f'Transducer output "{tg.output_string}" for input "{display_input}" '
                    "is not fully valid eng-arpabet as recognized by soundswallower."
                )
            return False
        elif is_ipa(out_lang):
            if is_panphon(tg.output_string, display_warnings=display_warnings):
                return True
            if display_warnings:
                display_input = original_input or tg.input_string
                LOGGER.warning(
                    f'Transducer output "{tg.output_string}" for input "{display_input}" is not fully valid {out_lang}.'
                )
            return False
        else:
            # No check implemented at this tier, just return True
            return True


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
    def tiers(self) -> List[TransductionGraph]:
        """A list of TransductionGraph objects for each tier in the CompositeTransducer"""
        return self._tiers

    @tiers.setter
    def tiers(self, value):
        raise ValueError(
            f"Sorry, you tried to change the tiers to {value} but they cannot be changed"
        )

    @property
    def edges(self) -> List:
        """List[List[Tuple[int, Optional[int]]]] of edges for each tier in the
        transformation.

        Note that this is unfortunately *not* the same between
        TransductionGraph and ComposedTransductionGraph.
        """
        return self._edges

    @edges.setter
    def edges(self, value):
        raise ValueError(
            f"Sorry, you tried to change the edges to {value} but they cannot be changed"
        )

    @property
    def debugger(self) -> List[list]:
        """List[List[List[dict]]]: A list of lists of lists of rules applied
        during the transformation. Useful for debugging.  Note that
        this is not the same between TransductionGraph and
        CompositeTransductionGraph.

        """
        return self._debugger

    @debugger.setter
    def debugger(self, value):
        raise ValueError(
            f"Sorry, you tried to change the debugger to {value} but they cannot be changed"
        )

    def pretty_edges(self):
        """List[List[Tuple[str, str]]] of edges for each tier, expressed as
        strings.

        Note that this is unfortunately *not* the same output between
        TransductionGraph and ComposedTransductionGraph.

        """
        pretty_edges = []
        for tier in self._tiers:
            pretty_edges.append(tier.pretty_edges())
        return pretty_edges

    def alignments(self) -> List[Tuple[int, Optional[int]]]:
        """Return list of alignments (input node index, output node index) for
        the full transduction.

        Note that this *is* the same between TransductionGraph and
        CompositeTransductionGraph.
        """
        composed = self.tiers[0].edges
        for tier in self.tiers[1:]:
            composed = compose_indices(composed, tier.edges)
        return composed

    def as_dict(self):
        return {
            "edges": self._edges,
            "input": self._input_string,
            "output": self._output_string,
            "input_nodes": self._input_nodes,
            "output_nodes": self._output_nodes,
        }

    def append(self, tg):
        if isinstance(tg, CompositeTransductionGraph):
            assert len(self._tiers) == len(tg._tiers)
            for i in range(len(self._tiers)):
                self._tiers[i].append(copy.deepcopy(tg.tiers[i]))
        else:
            for tier in self._tiers:
                tier.append(copy.deepcopy(tg))
        self.__init__(self.tiers)

    def __iadd__(self, tg):
        self.append(tg)
        return self

    def clear_debugger(self):
        self._debugger = []
        for tier in self._tiers:
            tier.clear_debugger()


class CompositeTransducer(BaseTransducer):
    """This class combines Transducer objects to form a CompositeTransducer object.

    Attributes:
        transducers (List[Transducer]): A list of Transducer objects to compose.
    """

    def __init__(self, transducers: List[Transducer]):
        self._transducers = transducers
        self.norm_form = transducers[0].norm_form if transducers else "none"

    def __repr__(self):
        return f"{self.__class__} between {self._transducers[0].mapping.in_lang} and {self._transducers[-1].mapping.out_lang}"

    def __call__(self, to_convert: str):
        return self.apply_rules(to_convert)

    @property
    def transducers(self):
        """Sequence of underlying Transducer objects"""
        return self._transducers

    @property
    def in_lang(self):
        """Input language node name"""
        return self._transducers[0].in_lang

    @property
    def out_lang(self):
        """Output language node name"""
        return self._transducers[-1].out_lang

    def apply_rules(self, to_convert: str):
        tg_list = []
        for transducer in self._transducers:
            tg = transducer(to_convert)
            tg_list.append(tg)
            to_convert = tg.output_string
        return CompositeTransductionGraph(tg_list)

    def check(
        self, tg: CompositeTransductionGraph, shallow=False, display_warnings=False
    ):
        assert len(self._transducers) == len(tg._tiers)
        if shallow:
            return self._transducers[-1].check(
                tg._tiers[-1],
                display_warnings=display_warnings,
                original_input=tg.input_string,
            )
        else:
            result = True
            for i, transducer in enumerate(self._transducers):
                if not transducer.check(
                    tg._tiers[i],
                    display_warnings=display_warnings,
                    original_input=tg.input_string,
                ):
                    # Don't short circuit if warnings are required
                    if display_warnings:
                        result = False
                    else:
                        return False
            return result


class TokenizingTransducer(BaseTransducer):
    """This class combines tokenization and transduction.

    This is particularly useful for lexicon mappings, which cannot
    handle more than a single word at a time.

    Attributes:
        transducer (Transducer): A Transducer object for the mapping part
        tokenizer (Tokenizer): A Tokenizer object to split the string before mapping
    """

    def __init__(
        self,
        transducer: Union[Transducer, CompositeTransducer],
        tokenizer: BaseTokenizer,
    ):
        self._transducer = transducer
        self._tokenizer = tokenizer

    def __call__(self, to_convert: str):
        # perform normalization before tokenizing, since it can change tokenization
        if self._transducer.norm_form:
            to_convert = normalize(to_convert, self._transducer.norm_form)

        # Initialize the transducer on an empty string so we can handle inputs
        # that start with a non-token correctly.
        tg = self._transducer("")
        tg.clear_debugger()  # clear the meaningless initial debugger

        for token in self._tokenizer.tokenize_text(to_convert):
            if token.is_word:
                word_tg = self._transducer(token.text)
                tg += word_tg
            else:
                non_word_tg = TransductionGraph(token.text)
                tg += non_word_tg
        return tg

    @property
    def transducer(self):
        """Underlying Transducer object"""
        return self._transducer

    @property
    def transducers(self) -> List[Transducer]:
        """Sequence of underlying Transducer objects"""
        return self._transducer.transducers

    @property
    def in_lang(self) -> str:
        """Input language node name"""
        return self._transducer.in_lang

    @property
    def out_lang(self) -> str:
        """Output language node name"""
        return self._transducer.out_lang

    def check(self, tg: TransductionGraph, shallow=False, display_warnings=False):
        # The obvious implementation fails, because we need to check only the words, not
        # the text between the words!
        # return self._transducer.check(tg) # <- complains about characters between words

        # So, sadly, we redo the work of transduction so we can check the words only, step
        # by step. I don't like this solution, but I don't see how to get around it.
        result = True
        for token in self._tokenizer.tokenize_text(tg.input_string):
            if token.is_word and not self._transducer.check(
                self._transducer(token.text),
                shallow,
                display_warnings=display_warnings,
            ):
                # Don't short circuit if warnings are required
                if display_warnings:
                    result = False
                else:
                    return False
        return result


def preserve_case(
    tg: TransductionGraph, case_equivalencies: Optional[Dict[str, str]] = None
) -> TransductionGraph:
    if case_equivalencies is None:
        case_equivalencies = {}
    reverse_case_equivalencies = {v: k for k, v in case_equivalencies.items()}
    all_lower_case_equivalencies = case_equivalencies.keys()
    all_upper_case_equivalencies = case_equivalencies.values()
    new_string = ""
    for item in tg.substring_alignments():
        in_sub = item[0]
        out_sub = item[1]
        any_in_upper = any(x.isupper() for x in in_sub)
        any_in_lower = any(x.islower() for x in in_sub)
        any_out_upper = any(x.isupper() for x in out_sub)
        any_out_lower = any(x.islower() for x in out_sub)
        # continue if character is un-caseable
        if (
            out_sub not in case_equivalencies
            and not any_out_upper
            and not any_out_lower
        ):
            new_string += out_sub
            continue
        # lower case using case equivalencies if they exist
        if (
            any_in_lower or in_sub in all_lower_case_equivalencies
        ) and out_sub in all_upper_case_equivalencies:
            new_string += reverse_case_equivalencies[out_sub]
            continue
        # upper case using case equivalencies if they exist
        elif (
            any_in_upper or in_sub in all_upper_case_equivalencies
        ) and out_sub in all_lower_case_equivalencies:
            new_string += case_equivalencies[out_sub]
            continue
        # change to upper if required
        if any_in_upper and any_out_lower:
            new_string += out_sub.upper()
            continue
        # change to lower if required
        if any_in_lower and any_out_upper:
            new_string += out_sub.lower()
            continue
        # just in case, append the out_sub
        new_string += out_sub
    tg.output_string = new_string
    return tg
