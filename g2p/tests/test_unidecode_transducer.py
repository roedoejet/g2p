#!/usr/bin/env python3

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
        self.assertEqual(
            tg.output_string, "EY T EY  N UW N AA V UW T  N OW N AA F OW T "
        )


if __name__ == "__main__":
    main()
