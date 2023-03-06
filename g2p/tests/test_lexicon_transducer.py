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
            tg.edges, [(0, 0), (1, 2), (1, 3), (2, 2), (2, 3), (4, 5), (5, 5)]
        )

    def test_eng_lexicon(self):
        m = Mapping(in_lang="eng", out_lang="eng-arpabet")
        self.assertEqual(m.kwargs["type"], "lexicon")
        t = Transducer(m)
        tg = t("hello")
        self.assertEqual(tg.output_string, "HH EH L OW ")
        self.assertEqual(
            tg.edges, [(0, 0), (0, 1), (1, 3), (1, 4), (2, 6), (3, 6), (4, 8), (4, 9)]
        )
        tg = t("you're")
        self.assertEqual(tg.output_string, "Y UW R ")
        self.assertEqual(
            tg.edges, [(0, 0), (1, 2), (1, 3), (2, 2), (2, 3), (4, 5), (5, 5)]
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
