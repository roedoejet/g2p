#!/usr/bin/env python

from unittest import TestCase, main

from g2p import make_g2p
from g2p.mappings import Mapping
from g2p.mappings.utils import normalize
from g2p.transducer import Transducer


class UnidecodeTransducerTest(TestCase):
    def test_unidecode_mapping(self):
        m = Mapping(type="unidecode")
        self.assertEqual(m.mapping, [])
        self.assertEqual(m.kwargs["type"], "unidecode")
        t = Transducer(m)
        tg = t("été Nunavut ᓄᓇᕗᑦ")
        self.assertEqual(tg.output_string, "ete Nunavut nonafot")

    def test_unidecode_g2p(self):
        transducer = make_g2p("und", "und-ascii")
        tg = transducer(normalize("éçà", "NFD"))
        self.assertEqual(tg.output_string, "eca")
        self.assertEqual(tg.edges, [(0, 0), (1, 0), (2, 1), (3, 1), (4, 2), (5, 2)])

        tg = transducer(normalize("éçà", "NFC"))
        self.assertEqual(tg.output_string, "eca")
        self.assertEqual(tg.edges, [(0, 0), (1, 1), (2, 2)])

    def test_unidecode_empty_output(self):
        transducer = make_g2p("und", "und-ascii")
        # \u0361 on its own gets deleted completely by unidecode
        tg = transducer("\u0361")
        self.assertEqual(tg.output_string, "")
        self.assertEqual(tg.edges, [])

    def test_unidecode_to_arpabet(self):
        transducer = make_g2p("und", "eng-arpabet")
        tg = transducer("été Nunavut ᓄᓇᕗᑦ")
        self.assertEqual(tg.output_string, "EY T EY N UW N AA V UW T N OW N AA F OW T ")
        # NOTE: spaces are deleted in the output, but they should be
        # retained in the input alignments and thus recoverable
        pe = tg.pretty_edges()
        self.assertIn((" ", " "), (tuple(x) for x in pe[0]))  # present in und-ascii
        self.assertNotIn((" ", " "), (tuple(x) for x in pe[1]))  # absent in und-ipa

    def test_unidecode_arabic_to_arpabet(self):
        transducer = make_g2p("und", "eng-arpabet")
        tg = transducer("السلام عليكم")
        self.assertEqual(tg.output_string, "L S L M L Y K M ")
        pe = tg.pretty_edges()
        self.assertIn((" ", " "), (tuple(x) for x in pe[0]))  # present in und-ascii
        self.assertNotIn((" ", " "), (tuple(x) for x in pe[1]))  # absent in und-ipa

    def test_unidecode_arabic_presentation_to_arpabet(self):
        transducer = make_g2p("und", "eng-arpabet")
        tg = transducer("ﺷﻜﺮﺍﹰ")
        self.assertEqual(tg.output_string, "S HH K D AA N ")
        # No input spaces, so no spaces in first transduction
        pe = tg.pretty_edges()
        self.assertNotIn((" ", " "), (tuple(x) for x in pe[0]))
        self.assertNotIn((" ", " "), (tuple(x) for x in pe[1]))

    def test_unidecode_kanji_to_arpabet(self):
        transducer = make_g2p("und", "eng-arpabet")
        tg = transducer("日本語")
        self.assertEqual(tg.output_string, "D IY B EY N Y UW ")
        pe = tg.pretty_edges()
        self.assertNotIn((" ", " "), (tuple(x) for x in pe[0]))
        self.assertNotIn((" ", " "), (tuple(x) for x in pe[1]))

    def test_unidecode_hanzi_to_arpabet(self):
        transducer = make_g2p("und", "eng-arpabet")
        tg = transducer("你们好!你们说汉语马?")
        self.assertEqual(
            tg.output_string,
            "N IY M EY N HH AA OW N IY M EY N S HH UW OW Y IY Y UW M AA HH ",
        )
        pe = tg.pretty_edges()
        self.assertNotIn((" ", " "), (tuple(x) for x in pe[0]))
        self.assertNotIn((" ", " "), (tuple(x) for x in pe[1]))


if __name__ == "__main__":
    main()
