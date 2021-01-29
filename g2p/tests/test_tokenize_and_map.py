#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from unittest import main, TestCase
import os
import g2p


class TokenizerTest(TestCase):
    """ Test suite for chaining tokenization and transduction """

    def setUp(self):
        pass

    def contextualize(self, word: str):
        return word + " " + word + " ," + word + ", " + word

    def test_tok_and_map_fra(self):
        """ Chaining tests: tokenize and map a string """
        transducer = g2p.make_g2p("fra", "fra-ipa")
        tokenizer = g2p.get_tokenizer("fra")
        # "teste" in isolation is at string and word end and beginning
        word_ipa = transducer("teste").output_string
        # "teste" followed by space or punctuation should be mapped to the same string
        string_ipa = g2p.tokenize_and_map(
            tokenizer, transducer, self.contextualize("teste")
        )
        self.assertEqual(string_ipa, self.contextualize(word_ipa))

    def test_tok_and_map_mic(self):
        transducer = g2p.make_g2p("mic", "mic-ipa")
        tokenizer = g2p.get_tokenizer("mic")
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

    def test_tokenizing_transducer_not_implemented(self):
        """ The tokenizing transducer returns a pseudo graph with several features not implemented
        """
        transducer = g2p.make_g2p("fra", "fra-ipa", tok_lang="fra")
        tg = transducer("teste")
        with self.assertRaises(ValueError):
            edges = tg.edges
        with self.assertRaises(ValueError):
            nodes = tg.output_nodes
        with self.assertRaises(ValueError):
            debugger = tg.debugger


if __name__ == "__main__":
    main()
