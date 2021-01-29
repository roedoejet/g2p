#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from unittest import main, TestCase
import os
import g2p.mappings.tokenizer as tok


class TokenizerTest(TestCase):
    """Test suite for tokenizing text in a language-specific way"""

    def setUp(self):
        pass

    def test_tokenize_fra(self):
        input = "ceci était 'un' test."
        tokenizer = tok.get_tokenizer("fra")
        tokens = tokenizer.tokenize_text(input)
        self.assertEqual(len(tokens), 8)
        self.assertTrue(tokens[0]["is_word"])
        self.assertEqual(tokens[0]["text"], "ceci")
        self.assertFalse(tokens[1]["is_word"])
        self.assertEqual(tokens[1]["text"], " ")
        self.assertTrue(tokens[2]["is_word"])
        self.assertEqual(tokens[2]["text"], "était")
        self.assertFalse(tokens[3]["is_word"])
        self.assertEqual(tokens[3]["text"], " '")
        self.assertTrue(tokens[4]["is_word"])
        self.assertEqual(tokens[4]["text"], "un")
        self.assertFalse(tokens[5]["is_word"])
        self.assertEqual(tokens[5]["text"], "' ")
        self.assertTrue(tokens[6]["is_word"])
        self.assertEqual(tokens[6]["text"], "test")
        self.assertFalse(tokens[7]["is_word"])
        self.assertEqual(tokens[7]["text"], ".")

    def test_tokenize_eng(self):
        input = "This is éçà test."
        tokenizer = tok.get_tokenizer("eng")
        tokens = tokenizer.tokenize_text(input)
        self.assertEqual(len(tokens), 8)
        self.assertTrue(tokens[0]["is_word"])
        self.assertEqual(tokens[0]["text"], "This")
        self.assertFalse(tokens[1]["is_word"])
        self.assertEqual(tokens[1]["text"], " ")

    def test_tokenize_win(self):
        """ win is easy to tokenize because win -> win-ipa exists and has ' in its inventory """
        input = "p'ōį̄ą"
        self.assertEqual(len(tok.get_tokenizer("fra").tokenize_text(input)), 3)

        tokenizer = tok.get_tokenizer("win")
        tokens = tokenizer.tokenize_text(input)
        self.assertEqual(len(tokens), 1)
        self.assertTrue(tokens[0]["is_word"])
        self.assertEqual(tokens[0]["text"], "p'ōį̄ą")

    def not_test_tokenize_tce(self):
        """ tce is hard to tokenize correctly because we have tce -> tce-equiv -> tce-ipa, and ' is
            only mapped in the latter.
            Challenges:
             - since tce->tce-ipa is not a direct mapping, we're probably getting a default
               tokenizer
             - we want to merge the input inventory of both tce->tce-equiv and tce-equiv->tce-ipa
               into just one joint inventory for the purpose of tokenization.
        """
        input = "ts'nj"
        self.assertEqual(len(tok.get_tokenizer("fra").tokenize_text(input)), 3)

        tokenizer = tok.get_tokenizer("tce")
        tokens = tokenizer.tokenize_text(input)
        self.assertEqual(len(tokens), 1)
        self.assertFalse(tokens[0]["is_word"])
        self.assertEqual(tokens[0]["text"], "ts'nj")

    def not_test_tokenize_tce_equiv(self):
        input = "ts'e ts`e ts‘e ts’"
        self.assertEqual(len(tok.get_tokenizer("fra").tokenize_text(input)), 14)
        self.assertEqual(len(tok.get_tokenizer("tce").tokenize_text(input)), 4)

    def not_test_tokenizer_identity_tce(self):
        self.assertNotEqual(tok.get_tokenizer("eng"), tok.get_tokenizer("fra"))
        # the following assertion currently fails because both get the default tokenizer
        self.assertNotEqual(tok.get_tokenizer("eng"), tok.get_tokenizer("tce"))

    def not_test_tokenize_kwk(self):
        """ kwk is easier than tce: we just need to use kwk-umista -> kwk-ipa, but that's not
            implemented yet.
        """
        self.assertEqual(
            len(tok.get_tokenizer("kwk-umista").tokenize_text("kwak'wala")), 1
        )


if __name__ == "__main__":
    main()
