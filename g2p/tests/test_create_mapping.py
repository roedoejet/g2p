#!/usr/bin/env python3

"""
Test all Mappings
"""

from unittest import TestCase, main

from g2p.mappings import Mapping
from g2p.mappings.create_ipa_mapping import (
    DISTANCE_METRICS,
    create_mapping,
    create_multi_mapping,
)
from g2p.transducer import Transducer


class MappingCreationTest(TestCase):
    def setUp(self):
        self.mappings = [
            {"in": "ɑ", "out": "AA"},
            {"in": "eː", "out": "EY"},
            {"in": "i", "out": "IY"},
            {"in": "u", "out": "UW"},
            {"in": "tʃ", "out": "CH"},
            {"in": "p", "out": "P"},
            {"in": "t", "out": "T"},
            {"in": "k", "out": "K"},
            {"in": "w", "out": "W"},
            {"in": "ɡ", "out": "G"},
            {"in": "ʒ", "out": "ZH"},
        ]
        self.target_mapping = Mapping(
            self.mappings, in_lang="eng-ipa", out_lang="eng-arpabet", out_delimiter=" "
        )

    def test_unigram_mappings(self):
        src_mappings = [
            {"in": "ᐃ", "out": "i"},
            {"in": "ᐅ", "out": "u"},
            {"in": "ᐊ", "out": "a"},
        ]
        src_mapping = Mapping(src_mappings, in_lang="crj", out_lang="crj-ipa")
        mapping = create_mapping(src_mapping, self.target_mapping)
        transducer = Transducer(mapping)
        self.assertEqual(transducer("a").output_string, "ɑ")
        self.assertEqual(transducer("i").output_string, "i")
        self.assertEqual(transducer("u").output_string, "u")

    def test_bigram_mappings(self):
        src_mappings = [
            {"in": "ᐱ", "out": "pi"},
            {"in": "ᑎ", "out": "ti"},
            {"in": "ᑭ", "out": "ki"},
        ]
        src_mapping = Mapping(src_mappings, in_lang="crj", out_lang="crj-ipa")
        mapping = create_mapping(src_mapping, self.target_mapping)
        transducer = Transducer(mapping)
        self.assertEqual(transducer("pi").output_string, "pi")
        self.assertEqual(transducer("ti").output_string, "ti")
        self.assertEqual(transducer("ki").output_string, "ki")

    def test_trigram_mappings(self):
        src_mappings = [
            {"in": "ᒋ", "out": "t͡ʃi"},
            {"in": "ᒍ", "out": "t͡ʃu"},
            {"in": "ᒐ", "out": "t͡ʃa"},
        ]
        src_mapping = Mapping(src_mappings, in_lang="crj", out_lang="crj-ipa")
        mapping = create_mapping(src_mapping, self.target_mapping)
        transducer = Transducer(mapping)
        self.assertEqual(transducer("t͡ʃi").output_string, "tʃi")
        self.assertEqual(transducer("t͡ʃu").output_string, "tʃu")
        self.assertEqual(transducer("t͡ʃa").output_string, "tʃɑ")

    def test_long_mappings(self):
        src_mappings = [
            {"in": "ᐧᐯ", "out": "pʷeː"},
            {"in": "ᐧᑌ", "out": "tʷeː"},
            {"in": "ᐧᑫ", "out": "kʷeː"},
        ]
        src_mapping = Mapping(src_mappings, in_lang="crj", out_lang="crj-ipa")
        mapping = create_mapping(src_mapping, self.target_mapping)
        transducer = Transducer(mapping)
        self.assertEqual(transducer("pʷeː").output_string, "pweː")
        self.assertEqual(transducer("tʷeː").output_string, "tweː")
        self.assertEqual(transducer("kʷeː").output_string, "kweː")

    def test_distance_errors(self):
        src_mappings = [{"in": "ᐃ", "out": "i"}]
        src_mapping = Mapping(src_mappings, in_lang="crj", out_lang="crj-ipa")
        # Exercise looking up distances in the known list
        with self.assertRaises(ValueError):
            _ = create_mapping(
                src_mapping, self.target_mapping, distance="not_a_distance"
            )
        with self.assertRaises(ValueError):
            _ = create_multi_mapping(
                [(src_mapping, "out")],
                [(self.target_mapping, "in")],
                distance="not_a_distance",
            )
        # White box testing: monkey-patch an invalid distance to validate the
        # second way we make sure distances are supported
        DISTANCE_METRICS.append("not_a_real_distance")
        with self.assertRaises(ValueError):
            _ = create_mapping(
                src_mapping, self.target_mapping, distance="not_a_real_distance"
            )
        with self.assertRaises(ValueError):
            _ = create_multi_mapping(
                [(src_mapping, "out")],
                [(self.target_mapping, "in")],
                distance="not_a_real_distance",
            )
        DISTANCE_METRICS.pop()

    def test_distances(self):
        # These mapppings are chosen to create different generated mappings
        # from the various distances.
        src_mappings = [
            {"in": "ᐧᐯ", "out": "pʷeː"},
            {"in": "ᒋ", "out": "t͡ʃi"},
            {"in": "ᕃ", "out": "ʁaj"},
        ]
        src_mapping = Mapping(src_mappings, in_lang="crj", out_lang="crj-ipa")
        mapping = create_mapping(src_mapping, self.target_mapping)
        # print("mapping", mapping, list(mapping), "distance", "default")
        self.assertTrue(isinstance(mapping, Mapping))
        set_of_mappings = {tuple(m["out"] for m in mapping)}
        for distance in DISTANCE_METRICS:
            mapping = create_mapping(
                src_mapping, self.target_mapping, distance=distance
            )
            # print("mapping", mapping, list(mapping), "distance", distance)
            self.assertTrue(isinstance(mapping, Mapping))
            set_of_mappings.add(tuple(m["out"] for m in mapping))

            mapping = create_multi_mapping(
                [(src_mapping, "out")], [(self.target_mapping, "in")], distance=distance
            )
            self.assertTrue(isinstance(mapping, Mapping))
            set_of_mappings.add(tuple(m["out"] for m in mapping))
        self.assertGreater(len(set_of_mappings), 3)


if __name__ == "__main__":
    main()
