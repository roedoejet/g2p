# -*- coding: utf-8 -*-

import os
import json
from gi2pi.tests.private.git_data_wrangler import returnLinesFromDocuments
from gi2pi.tests.private import __file__ as private_dir_f
from gi2pi.mappings import Mapping
from gi2pi.transducer import Transducer
from typing import List, Union



class Stats:
    def __init__(self, base_string: str, compare_string: str): 
        self.base_string = base_string
        self.compare_string = compare_string 
    
    def 


class Story:
    '''
    Initialize class with path (json,data,word document).
    Accesses story data.
    '''
    def __init__(self, path: str):
        '''
        The path should be to one of the three:
        - a word document containing the data
        - a json file containing the data
        - add actual data, not sure of file type?
        '''
        self.path = path
        
        if self.path.lower().endswith('.docx'):
            self.data = self.parse_word(self.path)
       
        elif self.path.lower().endswith('.json'):
            self.data = self.parse_json(self.path)
        
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
        Takes the path to a word document.
        Returns returnLinesFromDocuments.
        '''
        return returnLinesFromDocuments([self.path])

    def parse_json(self, path: str):
        '''
        Takes the path to a JSON file.
        Returns the lines as strings.
        '''
        with open(self.path, 'r') as f:
            json_data = json.load(f)
        return json_data

if __name__ == '__main__':
    mapping = Mapping(language={"lang": "git", "table": "Orthography (Deterministic)"}, case_sensitive=False)
    transducer = Transducer(mapping)
    private_dir = os.path.dirname(private_dir_f)
    story_json = Story(os.path.join(private_dir, 'BS - Dihlxw', 'Dihlxw Story 2013-04-29 for HD copy - clean.json'))  
    story_docx = Story(os.path.join(private_dir, 'BS - Dihlxw', 'Dihlxw Story 2013-04-29 for HD copy - clean.docx')) 
    breakpoint()


# Compare characters


# RETURN
# Failure percentage as an integer
# Count failures of the same type
