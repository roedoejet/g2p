# -*- coding: utf-8 -*-

from unittest import main, TestCase
import os
from g2p.cors import Correspondence
from g2p.transducer import Transducer
from datawrangler import data_wrangler

#remove ['~', '-', '='] from apa data

apa_text.replace(['~', '-', '='] , "")
apa_text = apa_text.replace

class GitTest(TestCase):
    ''' Test for Orthography to APA
    '''
  def setUp(self):
        git = {"name": "git",
               "tables": {
                   "Orthography (Step 1)": [                     
                       ("Hli dii ap wehl Gitwinhlguu'l, Git-anyaaw, wil mig\u0332oontxw Git-anyaaw.", "Hli diː æb wiɬ Gidwinɬɟulˀ, Gid-ænjæː|ʌw, wil miɟ\u0332ɔ|ontxʷ Gid-ænjæː|ʌw"),
                       ("Ii 'nithl sim'oogit Gwaas Hlaa'm 'nii ksg\u0332oog\u0332at ahl lax\u0332 g\u0332alts'ap tun.", "Ii ʔnidɬ simʔɔ|oːɟid Gwæː|ʌːs Hlæː|ʌːʔm ʔniː ksɟ\u0332ɔ|oːɟ\u0332æd æɬ læx\u0332 ɟ\u0332ælʦˀæb tun.") 
                   ],
                   "APA (no free variation)": [
                        ("", "\u026c\u0259 ti: \u0294\u0259p we=\u026c k\u0259tw\u0259n\u026ck\u02b7u:l\u0313 k\u0259t\u0294\u0259nya:w w\u0259l m\u0259qo:ntx\u02b7 k\u0259t-\u0294\u0259n-ya:w"),
                        ("", "\u0294i: n\u0313it=\u026c s\u0259m\u0294o:k\u0259t k\u02b7a:s-\u026ca:m\u0313 n\u0313i: ksqo:q-\u0259t \u0294\u0259=\u026c l\u0259\u03c7 q\u0259lc\u0313ap t=x\u02b7\u0259n")
                   ],
                   }
               }

        self.langs_to_test = [git]

    def test_io(self):
        # go through each language declared in the test case set up
        for lang in self.langs_to_test:
            lang_name = lang['name']
            # go through each table in the current lang
            for table in lang['tables'].keys():
                cors = Correspondence(
                    language={'lang': lang_name, 'table': table})
                transducer = Transducer(cors, as_is=True)
                # go through each input/output pair
                for pair in lang['tables'][table]:
                    # assert that the transduced first item in the tuple is equal to the second item in the tuple
                    self.assertEqual(transducer(pair[0]), pair[1])



if __name__ == "__main__":
    main()
