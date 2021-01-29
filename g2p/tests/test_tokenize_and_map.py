#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from unittest import main, TestCase
import os
import g2p


class TokenizerTest(TestCase):
    """ Test suite for chaining tokenization and transduction """

    def setUp(self):
        pass

    def test_tok_and_map_fra(self):
        """ Chaining tests: tokenize and map a string """
        input = "teste teste, teste"
        transducer = g2p.make_g2p("fra", "fra-ipa")
        tokenizer = g2p.get_tokenizer("fra")
        # "teste" in isolation is at string and word end and beginning
        word_ipa = transducer("teste").output_string
        # "teste" followed by space or punctuation should be mapped to the same string
        string_ipa = g2p.tokenize_and_map(tokenizer, transducer, "teste teste, teste")
        self.assertEqual(
            string_ipa, word_ipa + " " + word_ipa + ", " + word_ipa,
        )

    def test_tok_and_map_mic(self):
        transducer = g2p.make_g2p("mic", "mic-ipa")
        tokenizer = g2p.get_tokenizer("mic")
        word_ipa = transducer("sq").output_string
        string_ipa = g2p.tokenize_and_map(tokenizer, transducer, "sq sq ,sq, sq")
        self.assertEqual(
            string_ipa, word_ipa + " " + word_ipa + " ," + word_ipa + ", " + word_ipa,
        )


if __name__ == "__main__":
    main()
