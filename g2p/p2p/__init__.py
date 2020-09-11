#!/usr/bin/env python3
# -*- coding: utf-8 -*-

######################################################################
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
######################################################################

from __future__ import print_function, unicode_literals
from __future__ import division, absolute_import

from typing import List
import argparse
import json
import io

from panphon.xsampa import XSampa
import panphon.distance
from tqdm import tqdm

from g2p.mappings.utils import is_ipa, is_xsampa
from g2p.transducer import Transducer
from g2p.mappings import Mapping
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

def panphon_preprocess(inventory: List[str], is_xsampa: bool = False):
    xsampa_converter = XSampa()
    panphon_preprocessor = Transducer(Mapping(id='panphon_preprocessor'))
    new_inventory = []
    for x in inventory:
        if is_xsampa:
            x = xsampa_converter.convert(x)
        x = panphon_preprocessor(x).output_string
        new_inventory.append(x)
    return new_inventory

##################################
#
# Creating the mapping
#
#
#
###################################


def create_mapping(l1_mapping: Mapping, l2_mapping: Mapping) -> Mapping:
    ''' Create a mapping from the output of l1 and input of l2.
        Both must be either ipa or x-sampa.
    '''
    l1 = l1_mapping.kwargs['out_lang']
    l2 = l2_mapping.kwargs['in_lang']
    inv_l1 = l1_mapping.inventory("out")
    inv_l2 = l2_mapping.inventory()
    if not is_ipa(l1) and not is_xsampa(l1):
        LOGGER.warning("Unsupported orthography of inventory 1: %s"
                       " (must be ipa or x-sampa)",
                       l1)
    if not is_ipa(l2) and not is_xsampa(l2):
        LOGGER.warning("Unsupported orthography of inventory 2: %s"
                       " (must be ipa or x-sampa)",
                       l2)
    mapping = align_inventories(inv_l1["inventory"], inv_l2["inventory"],
                                is_xsampa(l1), is_xsampa(l2))

    output_mapping = Mapping(mapping, in_lang=l1, out_lang=l2)
    return output_mapping

def find_good_match(p1, inventory_l2, l2_is_xsampa=False):
    """Find a good sequence in inventory_l2 matching p1."""
    # The proper way to do this would be with some kind of beam search
    # through a determinized/minimized FST, but in the absence of that
    # we can do a kind of heurstic greedy search.  (we don't want any
    # dependencies outside of PyPI otherwise we'd just use OpenFST)
    dst = panphon.distance.Distance()
    p1_pseq = dst.fm.ipa_segs(p1)
    p2_pseqs = [dst.fm.ipa_segs(p)
                for p in panphon_preprocess(inventory_l2, l2_is_xsampa)]
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


def align_inventories(inventory_l1, inventory_l2,
                      l1_is_xsampa=False, l2_is_xsampa=False):
    mapping = []
    inventory_l1 = sorted(set(inventory_l1))
    inventory_l2 = list(set(inventory_l2))
    for i1, p1 in enumerate(tqdm(panphon_preprocess(inventory_l1,
                                                    l1_is_xsampa))):
        # we enumerate the strings because we want to save the original string
        # (e.g., 'kʷ') to the mapping, not the processed one (e.g. 'kw')
        good_match = find_good_match(p1, inventory_l2, l2_is_xsampa)
        mapping.append({"in": inventory_l1[i1], "out": good_match})
    return mapping
