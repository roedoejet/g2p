from unittest import main, TestCase
import os
from g2p.cors import Correspondence
from g2p.transducer import Transducer

class TransducerTest(TestCase):
    ''' Basic Transducer Test
    '''

    def setUp(self):
        self.test_cor = Correspondence([{'from': 'a', "to": 'b'}])
        self.test_cor_rev = Correspondence([{"from": 'a', "to": 'b'}], True)
        self.test_cor_moh = Correspondence(language={"lang": "moh", "table": "orth"})
        self.test_trans = Transducer(self.test_cor)
        self.test_trans_rev = Transducer(self.test_cor_rev)
        self.test_trans_moh = Transducer(self.test_cor_moh, True)

    def test_forward(self):
        self.assertEqual(self.test_trans('a'), "b")
        self.assertEqual(self.test_trans('b'), "b")

    def test_backward(self):
        self.assertEqual(self.test_trans_rev("b"), 'a')
        self.assertEqual(self.test_trans_rev("a"), 'a')
    
    def test_lang_import(self):
        self.assertEqual(self.test_trans_moh('kawennón:nis'), 'kawẽnonnis')

    def test_index(self):
        self.assertTrue(isinstance(self.test_trans('a', True), tuple))
        self.assertEqual(self.test_trans('a', True), ("b", [(1, 1)]))
        self.assertEqual(self.test_trans_moh('kawennón:nis', True), ('kawẽnonnis', [(1, 1), (2, 2), (3, 3), (5, 5), (6, 6), (7, 7), (8, 8), (9, 8), (10, 9), (11, 10), (12, 11)]))


if __name__ == "__main__":
    main()
    