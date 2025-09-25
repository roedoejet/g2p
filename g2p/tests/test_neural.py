#!/usr/bin/env python

from unittest import TestCase, main

from g2p import make_g2p


class NeuralTransducerTest(TestCase):
    """Basic Neural Transducer Test"""

    def test_neural(self):
        rules_g2p = make_g2p("str", "str-ipa")
        neural_g2p = make_g2p("str", "str-ipa", neural=True)
        result_rules = rules_g2p("SENĆOŦEN")
        self.assertEqual(result_rules.output_string, "sʌnt͡ʃɑθʌn")
        result_neural = neural_g2p("SENĆOŦEN")
        self.assertEqual(result_neural.output_string, "sənt͡ʃáθən")


if __name__ == "__main__":
    main()
