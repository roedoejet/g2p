from unittest import TestCase

from g2p import make_g2p
from g2p.mappings import Mapping
from g2p.transducer import Transducer

class TransitiveTest(TestCase):
    #TODO: This relies on transitive closure. Refactor to include in g2p from readalongs
    def setUp(self):
        self.test_conversion_data = [
            {'in_lang': 'git',
             'out_lang': 'eng-arpabet',
             'in_text': "K̲'ay",
             'out_text': 'K HH AE Y'},
            {'in_lang': 'git',
             'out_lang': 'eng-arpabet',
             'in_text': "guts'uusgi'y",
             'out_text': 'G UW T S HH UW S G IY HH Y'},
            {'in_lang': 'str',
             'out_lang': 'eng-arpabet',
             'in_text': 'X̱I¸ÁM¸',
             'out_text': 'SH W IY HH AH M HH'},
            {'in_lang': 'ctp',
             'out_lang': 'eng-arpabet',
             'in_text': 'Qneᴬ',
             'out_text': 'HH N EY'}
        ]

    def test_conversions(self):
        ''' Some conversion that were posing problems for readalongs.
            These might fail if the lookup tables change.
        '''
        for test in self.test_conversion_data:
            transducer = make_g2p(test['in_lang'], test['out_lang'])
            conversion = transducer(test['in_text'])
            self.assertEqual(conversion, test['out_text'])

    def test_reduced_indices(self):
        transducer = make_g2p('git', 'eng-arpabet')
        conversion = transducer("K̲'ay", index=True)
        self.assertEqual(conversion[1].reduced(), [
                         (2, 2), (3, 5), (4, 8), (5, 9)])         
        conversion1 = transducer("yukwhl", index=True)
        self.assertEqual(conversion1[1].reduced(), [
                         (1, 2), (2, 5), (3, 7), (4, 9), (6, 10)])