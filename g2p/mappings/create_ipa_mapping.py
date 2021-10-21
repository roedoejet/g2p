######################################################################
# Patrick Littell
#
# create_ipa_mapping.py
#
# Given two IPA inventories in JSON (either as dedicated inventory
# files or the input/output sides of mapping files), map the first
# onto the second by use of panphon's phonetic distance calculators.
#
# The resulting mappings are used just like other mappings: to make
# converters and pipelines of converters in convert_orthography.py
#
# AP Note: Taken from ReadAlongs-Studio and implemented with G2P formatting
######################################################################

from __future__ import print_function, unicode_literals
from __future__ import division, absolute_import

from copy import deepcopy
import json
import os

from tqdm import tqdm
import yaml

from g2p.mappings.utils import is_ipa, is_xsampa, IndentDumper
from g2p.transducer import Transducer
from g2p.mappings import Mapping
from g2p.mappings.langs.utils import getPanphonDistanceSingleton
from g2p.log import LOGGER

#################################
#
# Preprocessing:
#
# Panphon can only match a single segment to another segment, rather
# than (say) try to combine two segments to better match the features.
# For example, you might want "kʷ" to match to "kw", but Panphon will
# only match the "kʷ" to "k" and consider the "w" to be a dropped
# character.  In order to get around this, we preprocess strings so
# that common IPA segments that you might expect map to two characters
# in another language, like affricates or rounded consonants, are
# treated as two characters rather than one.
#
#################################
_xsampa_converter = None  # Cache this but create it only of needed

def process_character(p, is_xsampa=False):
    if is_xsampa:
        if _xsampa_converter is None:
            from panphon.xsampa import XSampa  # Expensive import, do it only when needed
            _xsampa_converter = XSampa()
        p = _xsampa_converter.convert(p)
    panphon_preprocessor = Transducer(Mapping(id='panphon_preprocessor'))
    return panphon_preprocessor(p).output_string


def process_characters(inv, is_xsampa=False):
    return [process_character(p, is_xsampa) for p in inv]

##################################
#
# Creating the mapping
#
#
#
###################################


def create_mapping(mapping_1: Mapping, mapping_2: Mapping, mapping_1_io: str = 'out', mapping_2_io: str = 'in') -> Mapping:
    """Create a mapping from mapping_1's output inventory to mapping_2's input inventory"""

    map_1_name = mapping_1.kwargs[f'{mapping_1_io}_lang']
    map_2_name = mapping_2.kwargs[f'{mapping_2_io}_lang']
    if not is_ipa(map_1_name) and not is_xsampa(map_1_name):
        LOGGER.warning("Unsupported orthography of inventory 1: %s"
                       " (must be ipa or x-sampa)",
                       map_1_name)
    if not is_ipa(map_2_name) and not is_xsampa(map_2_name):
        LOGGER.warning("Unsupported orthography of inventory 2: %s"
                       " (must be ipa or x-sampa)",
                       map_2_name)
    l1_is_xsampa, l2_is_xsampa = is_xsampa(map_1_name), is_xsampa(map_2_name)
    mapping = align_inventories(mapping_1.inventory(mapping_1_io), mapping_2.inventory(mapping_2_io),
                                l1_is_xsampa, l2_is_xsampa)

    # Initialize mapping with input language parameters (as_is,
    # case_sensitive, prevent_feeding, etc)
    config = mapping_1.kwargs.copy()
    # Fix up names, etc.
    if 'authors' in config:
        del config['authors']
    if 'display_name' in config:
        del config['display_name']
    if 'language_name' in config:
        del config['language_name']
    config['in_lang'] = map_1_name
    config['out_lang'] = map_2_name
    config['mapping'] = mapping
    mapping = Mapping(**config)
    return mapping


def align_inventories(inventory_l1, inventory_l2,
                      l1_is_xsampa=False, l2_is_xsampa=False):
    """Align inventories by finding a good sequence in inventory_l2 for each
    character in inventory_l1"""

    # find_good_match() is a function inside align_inventories() because it
    # lets us initialize dst and ps_pseqs globally once, yielding a roughly 8x
    # speed inprovements over the previous version of the code.

    # Initializing panphon.distance.Distance() is expensive, so do it just once
    dst = getPanphonDistanceSingleton()
    # Initializing p2_pseqs is expensive, so do it only once per call to align_inventories()
    p2_pseqs = [dst.fm.ipa_segs(p)
                for p in process_characters(inventory_l2, l2_is_xsampa)]

    def find_good_match(p1, inventory_l2, l2_is_xsampa=False):
        """Find a good sequence in inventory_l2 matching p1."""

        # The proper way to do this would be with some kind of beam search
        # through a determinized/minimized FST, but in the absence of that
        # we can do a kind of heurstic greedy search.  (we don't want any
        # dependencies outside of PyPI otherwise we'd just use OpenFST)

        p1_pseq = dst.fm.ipa_segs(p1)

        i = 0
        good_match = []
        while i < len(p1_pseq):
            best_input = ""
            best_output = -1
            best_score = 0xdeadbeef
            for j, p2_pseq in enumerate(p2_pseqs):
                # FIXME: Should also consider the (weighted) possibility
                # of deleting input or inserting any segment (but that
                # can't be done with a greedy search)
                if len(p2_pseq) == 0:
                    LOGGER.warning('No panphon mapping for %s - skipping',
                                   inventory_l2[j])
                    continue
                e = min(i + len(p2_pseq), len(p1_pseq))
                input_seg = p1_pseq[i:e]
                score = dst.weighted_feature_edit_distance(''.join(input_seg),
                                                           ''.join(p2_pseq))
                # Be very greedy and take the longest match
                if (score < best_score
                    or score == best_score
                        and len(input_seg) > len(best_input)):
                    best_input = input_seg
                    best_output = j
                    best_score = score
            LOGGER.debug('Best match at position %d: %s => %s',
                         i, best_input, inventory_l2[best_output])
            good_match.append(inventory_l2[best_output])
            i += len(best_input)  # greedy!
        return ''.join(good_match)

    mapping = []
    pbar = tqdm(total=100)
    step = 1/len(inventory_l1)*100
    for i1, p1 in enumerate(process_characters(inventory_l1,
                                               l1_is_xsampa)):
        # we enumerate the strings because we want to save the original string
        # (e.g., 'kʷ') to the mapping, not the processed one (e.g. 'kw')
        good_match = find_good_match(p1, inventory_l2, l2_is_xsampa)
        mapping.append({"in": inventory_l1[i1], "out": good_match})
        pbar.update(step)
    pbar.close()
    return mapping
