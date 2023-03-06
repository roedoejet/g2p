#!/usr/bin/env python

import os
from unittest import TestCase, main

from g2p import make_g2p
from g2p.mappings import Mapping
from g2p.tests.public import __file__ as public_data
from g2p.transducer import Transducer


class LexiconTransducerTest(TestCase):
    def test_lexicon_mapping(self):
        m = Mapping(
            type="lexicon",
            case_sensitive=False,
            out_delimiter=" ",
            alignments=os.path.join(
                os.path.dirname(public_data), "mappings", "hello.aligned.txt"
            ),
        )
        self.assertEqual(m.mapping, [])
        self.assertEqual(m.kwargs["type"], "lexicon")
        t = Transducer(m)
        tg = t("hello")
        self.assertEqual(tg.output_string, "HH EH L OW ")
        self.assertEqual(
            tg.edges, [(0, 0), (0, 1), (1, 3), (1, 4), (2, 6), (3, 6), (4, 8), (4, 9)]
        )
        tg = t("you're")
        self.assertEqual(tg.output_string, "Y UH R ")
        self.assertEqual(
            tg.edges,
            [(0, 0), (1, 2), (1, 3), (2, 2), (2, 3), (3, None), (4, 5), (5, 5)],
        )

    def test_eng_lexicon(self):
        m = Mapping(in_lang="eng", out_lang="eng-arpabet")
        self.assertEqual(m.kwargs["type"], "lexicon")
        t = Transducer(m)
        tg = t("hello")
        self.assertEqual(tg.output_string, "HH AH L OW ")
        self.assertEqual(
            tg.edges, [(0, 0), (0, 1), (1, 3), (1, 4), (2, 6), (3, 6), (4, 8), (4, 9)]
        )
        tg = t("you're")
        self.assertEqual(tg.output_string, "Y UW R ")
        self.assertEqual(
            tg.edges, [(0, 0), (1, 2), (1, 3), (2, 2), (2, 3), (4, 5), (5, 5)]
        )
        self.assertEqual(tg.output_string, "hʌloʊ")
        tg = t("change")
        self.assertEqual(tg.output_string, "tʃeɪndʒ")
        self.assertEqual(tg.input_string, "change")
        self.assertEqual(
            tg.edges,
            [
                (0, 0),
                (0, 1),
                (1, None),
                (2, 2),
                (2, 3),
                (3, 4),
                (4, 5),
                (4, 6),
                (5, None),
            ],
        )
        # Test insertions and deletions
        tg = t("chain")
        # These aligments are weird but they are the ones EM gave us
        self.assertEqual(tg.output_string, "tʃeɪn")
        self.assertEqual(tg.input_string, "chain")
        self.assertEqual(tg.edges, [(0, 0), (0, 1), (1, None), (2, 2), (3, 3), (4, 4)])
        tg = t("xtra")
        self.assertEqual(tg.output_string, "ɛkstɹʌ")
        self.assertEqual(tg.input_string, "xtra")
        self.assertEqual(tg.edges, [(None, 0), (0, 1), (0, 2), (1, 3), (2, 4), (3, 5)])
        pe = tg.pretty_edges()
        self.assertEqual(
            pe,
            [[None, "ɛ"], ["x", "k"], ["x", "s"], ["t", "t"], ["r", "ɹ"], ["a", "ʌ"]],
        )

    def test_eng_transducer(self):
        transducer = make_g2p("eng", "eng-arpabet")
        tg = transducer("hello")
        self.assertEqual(tg.output_string, "HH EH L OW ")
        self.assertEqual(
            tg.edges, [(0, 0), (0, 1), (1, 3), (1, 4), (2, 6), (3, 6), (4, 8), (4, 9)]
        )


if __name__ == "__main__":
    main()
