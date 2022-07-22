#!/usr/bin/env python3

from unittest import TestCase, main

import g2p


class TokenizeAndMapTest(TestCase):
    """Test suite for chaining tokenization and transduction"""

    def setUp(self):
        pass

    def contextualize(self, word: str):
        return word + " " + word + " ," + word + ", " + word

    def test_tok_and_map_fra(self):
        """Chaining tests: tokenize and map a string"""
        transducer = g2p.make_g2p("fra", "fra-ipa")
        tokenizer = g2p.make_tokenizer("fra")
        # "teste" in isolation is at string and word end and beginning
        word_ipa = transducer("teste").output_string
        # "teste" followed by space or punctuation should be mapped to the same string
        string_ipa = g2p.tokenize_and_map(
            tokenizer, transducer, self.contextualize("teste")
        )
        self.assertEqual(string_ipa, self.contextualize(word_ipa))

    def test_tok_and_map_mic(self):
        transducer = g2p.make_g2p("mic", "mic-ipa")
        tokenizer = g2p.make_tokenizer("mic")
        word_ipa = transducer("sq").output_string
        string_ipa = g2p.tokenize_and_map(
            tokenizer, transducer, self.contextualize("sq")
        )
        self.assertEqual(string_ipa, self.contextualize(word_ipa))

    def test_tokenizing_transducer(self):
        ref_word_ipa = g2p.make_g2p("mic", "mic-ipa")("sq").output_string
        transducer = g2p.make_g2p("mic", "mic-ipa", tok_lang="mic")
        word_ipa = transducer("sq").output_string
        self.assertEqual(word_ipa, ref_word_ipa)
        string_ipa = transducer(self.contextualize("sq")).output_string
        self.assertEqual(string_ipa, self.contextualize(ref_word_ipa))

    def test_tokenizing_transducer_chain(self):
        transducer = g2p.make_g2p("fra", "eng-arpabet", tok_lang="fra")
        self.assertEqual(
            self.contextualize(transducer("teste").output_string),
            transducer(self.contextualize("teste")).output_string,
        )

    def test_tokenizing_transducer_debugger(self):
        transducer = g2p.make_g2p("fra", "fra-ipa", tok_lang="fra")
        debugger = transducer("ceci est un test.").debugger
        self.assertEqual(len(debugger), 4)

    def test_tokenizing_transducer_edges(self):
        transducer = g2p.make_g2p("fra", "fra-ipa", tok_lang="fra")
        edges = transducer("est est").edges
        # est -> ɛ, so edges are (0, 0), (1, 0), (2, 0) for each "est", plus the
        # space to the space, and the second set of edges being offset
        ref_edges = [(0, 0), (1, 0), (2, 0), (3, 1), (4, 2), (5, 2), (6, 2)]
        self.assertEqual(edges, ref_edges)

    def test_tokenizing_transducer_edges2(self):
        ref_edges = g2p.make_g2p("fra", "fra-ipa")("ça ça").edges
        edges = g2p.make_g2p("fra", "fra-ipa", tok_lang="fra")("ça ça").edges
        self.assertEqual(edges, ref_edges)

    def test_tokenizing_transducer_edge_chain(self):
        transducer = g2p.make_g2p("fra", "eng-arpabet", tok_lang="fra")
        edges = transducer("est est").edges
        ref_edges = [
            # "est est" -> "ɛ ɛ"
            [(0, 0), (1, 0), (2, 0), (3, 1), (4, 2), (5, 2), (6, 2)],
            # "ɛ ɛ" -> "ɛ ɛ"
            [(0, 0), (1, 1), (2, 2)],
            # "ɛ ɛ" -> "EH  EH "
            [(0, 0), (0, 1), (0, 2), (1, 3), (2, 4), (2, 5), (2, 6)],
        ]
        self.assertEqual(edges, ref_edges)

    def test_tokenizing_transducer_edge_spaces(self):
        transducer = g2p.make_g2p("fra", "eng-arpabet", tok_lang="fra")
        edges = transducer("  a, ").edges
        ref_edges = [
            # "  a, " -> "  a, "
            [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)],
            # "  a, " -> "  ɑ, "
            [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)],
            # "  ɑ, " -> "  AA , "
            [(0, 0), (1, 1), (2, 2), (2, 3), (2, 4), (3, 5), (4, 6)],
        ]
        self.assertEqual(edges, ref_edges)


if __name__ == "__main__":
    main()
