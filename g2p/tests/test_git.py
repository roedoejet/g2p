# -*- coding: utf-8 -*-

import os
from unittest import main, TestCase
from g2p.mappings import Mapping
from g2p.transducer import CompositeTransducer, Transducer
# Will cause errors on machines without private data
from g2p.tests.private.git_data_wrangler import returnLinesFromDocuments
from g2p.tests.private import __file__ as private_dir
from typing import List
from g2p.log import LogCounter, TEST_LOGGER as logger


def scrub_text(txt: str, to_scrub: List[str] = ['=', '-', '~']) -> str:
    ''' Given some text (txt), scrub all characters in list (to_scrub) from text.
    '''
    for char in to_scrub:
        txt = txt.replace(char, '')
    return txt


class GitTest(TestCase):
    ''' Test for Orthography (Deterministic) to APA
    '''

    def setUp(self):
        # set up log counter
        logger.exception = LogCounter(logger.exception)
       # git = {"name": "git",
       #        "tables": {
       #            "Orthography (Deterministic)": [
       #                ("Hli dii ap wehl Gitwinhlguu'l, Git-anyaaw, wil mig\u0332oontxw Git-anyaaw.",
       #                 "Hli diː æb wiɬ Gidwinɬɟulˀ, Gid-ænjæːw, wil miɟ\u0332untxʷ Gid-ænjæːw."),
       #                ("Ii 'nithl sim'oogit Gwaas Hlaa'm 'nii ksg\u0332oog\u0332at ahl lax\u0332 g\u0332alts'ap tun.",
       #                 "Ii ʔnidɬ simʔɔɟid Gwæːs Hlæːʔm ʔniː ksɟ\u0332ɔɟ\u0332æd æɬ læx\u0332 ɟ\u0332ælʦˀæb tun.")
       #            ],
       #            "APA": [
       #                ("", "\u026c\u0259 ti: \u0294\u0259p we=\u026c k\u0259tw\u0259n\u026ck\u02b7u:l\u0313 k\u0259t\u0294\u0259nya:w w\u0259l m\u0259qo:ntx\u02b7 k\u0259t-\u0294\u0259n-ya:w"),
       #                ("", "\u0294i: n\u0313it=\u026c s\u0259m\u0294o:k\u0259t k\u02b7a:s-\u026ca:m\u0313 n\u0313i: ksqo:q-\u0259t \u0294\u0259=\u026c l\u0259\u03c7 q\u0259lc\u0313ap t=x\u02b7\u0259n")
       #            ],
       #        }
       #        }
        self.formatted_data = returnLinesFromDocuments(
            [
                os.path.join(os.path.dirname(private_dir),
                             'VG - Nass Volcano',
                             '2016-07-12 Nass River Volcano - CF edit VG check2.docx'),
                #os.path.join(os.path.dirname(private_dir),
                #             'VG - Kitwancool Surveyed',
                #             '2014-01-29 VG Kitwancool Reserve Surveyed CAF edit3 for HD.docx'),
                #os.path.join(os.path.dirname(private_dir),
                #             'VG - Founding of Gitanyow',
                #             '2017-01-27 VG The Founding of Git-anyaaw - HD comments more fixes.docx'),
                #os.path.join(os.path.dirname(private_dir),
                #             "HH - Mystery Story",
                #             "15-10-31 HH Hector's Betl'a Betl' - 4 checks_AP.docx"),
                #os.path.join(os.path.dirname(private_dir),
                #             "HH - Win Bekwhl",
                #             "2014-10-22 HH Win Bexwhl K'amk'siwaa - 2016-04-22 CAF 1st gloss.docx"),
                #os.path.join(os.path.dirname(private_dir),
                #             "BS - Dihlxw",
                #             "Dihlxw Story 2013-04-29 for HD copy - clean.docx"),
            ])

        # Declare all of our mappings needed
        self.orth_to_ipa = Mapping(
            language={"lang": "git", "table": "Orthography (Deterministic)"})

        self.orth_to_ipa_transducer = Transducer(self.orth_to_ipa, as_is=True)

        self.ipa_to_orth = Mapping(
            language={"lang": "git", "table": "Orthography (Deterministic)"}, reverse=True)

        self.ipa_to_orth_transducer = Transducer(self.ipa_to_orth)

        self.apa_to_ipa = Mapping(
            language={"lang": "git", "table": "APA"})

        self.apa_to_ipa_transducer = Transducer(self.apa_to_ipa, as_is=True)

        self.ipa_to_apa = Mapping(
            language={"lang": "git", "table": "APA"}, reverse=True)

        self.ipa_to_apa_transducer = Transducer(self.ipa_to_apa)

        self.orth_to_apa_transducer = CompositeTransducer(
            [self.orth_to_ipa_transducer, self.ipa_to_apa_transducer])
        self.apa_to_orth_transducer = CompositeTransducer(
            [self.apa_to_ipa_transducer, self.ipa_to_orth_transducer])

    def test_orth_to_apa(self):     
        for title, story in self.formatted_data.items():
            for line in story:
                try:
                    self.assertEqual(self.orth_to_apa_transducer(
                        line['ortho']), scrub_text(line['apa']))
                except:
                    logger.exception(f"{self.orth_to_apa_transducer(line['ortho'])} is not equal to {scrub_text(line['apa'])}")
        logger.info("The logger came across %s exceptions", logger.exception.count)


    def test_apa_to_orth(self):
        for title, story in self.formatted_data.items():
            for line in story:
                try:
                    self.assertEqual(self.apa_to_orth_transducer(
                        scrub_text(line['apa'])), line['ortho'])
                except:
                    logger.exception(f"{self.orth_to_apa_transducer(line['ortho'])} is not equal to {scrub_text(line['apa'])}")
        logger.info("The logger came across %s exceptions", logger.exception.count)

if __name__ == "__main__":
    main()
