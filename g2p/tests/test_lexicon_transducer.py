#!/usr/bin/env python

import os
from unittest import TestCase, main

import g2p
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
        self.assertEqual(tg.output_string, "HH EH L OW")
        tg = t("you're")
        self.assertEqual(tg.output_string, "Y UH R")

    def test_eng_lexicon(self):
        m = Mapping(
            type="lexicon",
            case_sensitive=False,
            out_delimiter=" ",
            alignments=os.path.join(
                os.path.dirname(g2p.__file__),
                "mappings",
                "langs",
                "eng",
                "cmudict_SPHINX_40.aligned.txt",
            ),
        )
        self.assertEqual(m.mapping, [])
        self.assertEqual(m.kwargs["type"], "lexicon")
        t = Transducer(m)
        tg = t("hello")
        self.assertEqual(tg.output_string, "HH EH L OW")
        tg = t("you're")
        self.assertEqual(tg.output_string, "Y UW R")


if __name__ == "__main__":
    main()
