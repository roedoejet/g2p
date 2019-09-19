#!/usr/bin/env python3
# -*- coding: utf-8 -*-

########################################################
# © Patrick Littell
# 
# Transpile mapping to FST source
#
# We're not currently using this module, but
# once we have index-preserving finite-state G2P,
# this will take the mapping files and turn them into
# FSTs.
#
# AP TODO: This has to be refactored to work with g2p.mappings.Mapping objects
########################################################

from __future__ import print_function, unicode_literals, division
from io import open
import argparse
import json


def make_header_comments(mapping):
    lines = []
    lines.append("#################################")
    lines.append("#")
    lines.append("# FST converting from %s-%s to %s-%s"
                 % (mapping["in_metadata"]["lang"],
                    mapping["in_metadata"]["orth"],
                    mapping["out_metadata"]["lang"],
                    mapping["out_metadata"]["orth"]))
    lines.append("#")
    authors = " & ".join(mapping["authors"])
    lines.append("# Based on a mapping by %s " % (authors,))
    lines.append("# created %s" % mapping["created"])
    lines.append("# last modified %s" % mapping["last_modified"])
    lines.append("#")
    lines.append("#################################")
    lines.append('')
    return lines


def escape_xfst_specials(s):
    return s.replace(
        "-", "%-").replace(
            "0", "%0").replace(
                "|", "%|").replace(":", "%:")


def camelize(s):
    return s[0].upper() + s[1:].lower()


def get_identifier_prefix(mapping):
    return


def compile_correspondences(mapping):
    lines = []
    corrs = [(escape_xfst_specials(x["in"]), escape_xfst_specials(x["out"]))
             for x in mapping["map"]]
    corrs = ["{%s}:{%s}" % (x, y) for x, y in corrs]
    identifier = camelize(mapping["in_metadata"]["lang"]) + \
        camelize(mapping["in_metadata"]["orth"]) + "To" + \
        camelize(mapping["out_metadata"]["lang"]) + \
        camelize(mapping["out_metadata"]["orth"])
    lines.append("define " + identifier + " [" + "|".join(corrs) + "]* ;")
    lines.append("push " + identifier)
    return lines


def go(mapping_filename, output_filename):
    with open(mapping_filename, "r", encoding="utf-8") as fin:
        mapping = json.load(fin)
    lines = "\n".join(make_header_comments(mapping) +
                      compile_correspondences(mapping))
    with open(output_filename, "w", encoding="utf-8") as fout:
        fout.write(lines)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Create an inventory file from a mapping file')
    parser.add_argument('mapping', type=str, help='Mapping filename')
    parser.add_argument('output', type=str, help='Output inventory filename')
    args = parser.parse_args()
    go(args.mapping, args.output)
