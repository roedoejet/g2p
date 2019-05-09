from unittest import main, TestCase
import os
from g2p.cors import Correspondence
from g2p.transducer import Transducer

class TransducerTest(TestCase):
    ''' Basic Transducer Test
    '''

    def setUp(self):
        self.test_cor = Correspondence('/Users/pinea/G2P/g2p/cors/langs/hei/doulos.csv')
        self.test_cor_rev = Correspondence('/Users/pinea/G2P/g2p/cors/langs/hei/doulos.csv', True)
        self.test_trans = Transducer(self.test_cor)
        self.test_trans_rev = Transducer(self.test_cor_rev)

    def test_forward(self):
        self.assertEqual(self.test_trans('¥'), "y̓")

    def test_backward(self):
        self.assertEqual(self.test_trans_rev("y̓"), '¥')

if __name__ == "__main__":
    main()