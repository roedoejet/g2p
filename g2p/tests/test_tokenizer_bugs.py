#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from unittest import main, TestCase
from g2p.log import LOGGER
import os

import g2p.mappings.tokenizer as tok

class TokenizerTestBugs(TestCase):
    """ Test suite for tokenizing text in a language-specific way.
        These test cases where separated from TokenizerText (test_tokenize.py)
        because they won't pass until issue #46 is resolved, so we don't want
        them included in the "./run.py dev" yet or run by travis-ci.
    """

    def setUp(self):
        pass

    def test_tokenize_tce(self):
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
        self.assertTrue(tokens[0]["is_word"])
        self.assertEqual(tokens[0]["text"], "ts'nj")

    def test_tokenize_tce_equiv(self):
        input = "ts'e ts`e ts‘e ts’"
        self.assertEqual(len(tok.get_tokenizer("fra").tokenize_text(input)), 14)
        tce_tokens = tok.get_tokenizer("tce").tokenize_text(input)
        #LOGGER.warning([x["text"] for x in tce_tokens])
        self.assertEqual(len(tok.get_tokenizer("tce").tokenize_text(input)), 7)

    def test_tokenizer_identity_tce(self):
        self.assertNotEqual(tok.get_tokenizer("eng"), tok.get_tokenizer("fra"))
        # the following assertion currently fails because both get the default tokenizer
        self.assertNotEqual(tok.get_tokenizer("eng"), tok.get_tokenizer("tce"))

    def test_tokenize_kwk(self):
        """ kwk is easier than tce: we just need to use kwk-umista -> kwk-ipa, but that's not
            implemented yet.
        """
        self.assertEqual(len(tok.get_tokenizer("kwk-umista").tokenize_text("kwak'wala")), 1)


if __name__ == "__main__":
    main()
