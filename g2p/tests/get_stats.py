# -*- coding: utf-8 -*-

import os
import json
from g2p.tests.private.git_data_wrangler import returnLinesFromDocuments
from g2p.tests.private import __file__ as private_dir_f
from g2p.mappings import Mapping
from g2p.transducer import Transducer
from typing import List, Union


# origin of data
class Stats:  # You should think about classes as objects. Functions do things and classes are things. So I would reframe this as a 'Stats' object
    # you could name this compare string? or anything really. See how I'm adding the type definitions for what these inputs are?
    def __init__(self, base_string: str, compare_string: str):
        # Here is where you should put data that you might need in the rest of your methods
        self.base_string = base_string
        self.compare_string = compare_string
        pass


class Story:
    ''' Here is where we put info about the Story class
    '''
    # initialize with path (json,data,word document)
    # and be able to initialize it with a path

    def __init__(self, path: str):
        self.path = path
        # the path should be to one of the three:
        # - a word document containing the data
        if self.path.lower().endswith('.docx'):
            self.data = self.parse_word(self.path)
        # - a json file containing the data
        elif self.path.lower().endswith('.json'):
            self.data = self.parse_json(self.path)
        # add actual data, not sure of file type?
        else:
            raise TypeError("Not a supported file type")

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    # TODO: Document or delete!
    def length_of_line(self, line_index, line_key):
        return len(self.data[line_index][line_key])

    def parse_word(self, path: str):
        '''
        return APA line from word document
        '''
        return returnLinesFromDocuments([path])

    def parse_json(self, path: str):
        '''
        return parsed JSON
        '''
        with open(path, 'r') as f:
            json_data = json.load(f)
        return json_data

if __name__ == '__main__':
    mapping = Mapping(language={"lang": "git", "table": "Orthography (Deterministic)"}, case_sensitive=False)
    transducer = Transducer(mapping)
    private_dir = os.path.dirname(private_dir_f)
    story_json = Story(os.path.join(private_dir, 'BS - Dihlxw',
                                    'Dihlxw Story 2013-04-29 for HD copy - clean.json'))
    for line in story_json:
        transduced = transducer.apply_rules(line['ortho'])
        print(transduced)
    story_docx = Story(os.path.join(private_dir, 'BS - Dihlxw',
                                    'Dihlxw Story 2013-04-29 for HD copy - clean.docx'))


# functions should be lower snake case, have a look here: https://www.python.org/dev/peps/pep-0008/

    # self.formatted_data = returnLinesFromDocuments

# Scrub
# def scrub_text(txt: str, to_scrub: List[str] = ['=', '-', '~']) -> str:
#     ''' Given some text (txt), scrub all characters in list (to_scrub) from text.
#     '''
#     for char in to_scrub:
#         txt = txt.replace(char, '')
#     return txt


# Count characters in APA line (Expected AND transduced)
# def count_char():
#     len(line['apa']) #and len(self.orth_to_apa_transducer = CompositeTransducer([self.orth_to_ipa_transducer, self.ipa_to_apa_transducer]))??
    # if len() != len()

    # return


# Compare characters


# RETURN
# Failure percentage as an integer
# Count failures of the same type
