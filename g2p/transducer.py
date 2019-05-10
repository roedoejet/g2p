'''
Class for performing transductions based on correspondences

'''

from typing import List
import random
import re
from g2p.cors import Correspondence

class Transducer():
    '''Class for performing transductions based on correspondences
    '''
    def __init__(self, cors: List[Correspondence], as_is: bool = False):
        if not as_is:
            # process intermediate to prevent feeding
            cors = self.process_intermediate(cors)
            # sort by reverse len
            cors.sort(key=len, reverse=True)

        for cor in cors:
            cor['match_pattern'] = self.rule_to_regex(cor)
        
        self.cor_list = cors

    def __call__(self, to_parse):
        return self.apply_rules(to_parse)
        
    def process_intermediate(self, cor_list):
        # To prevent feeding
        for cor in cor_list:
            # if output exists as input for another cor
            if cor['to'] in [temp_cor['from'] for temp_cor in cor_list]:
                # assign a random, unique character as a temporary value. this could be more efficient
                random_char = chr(random.randrange(9632, 9727))
                # make sure character is unique
                if [temp_char for temp_char in cor_list if 'temp' in list(temp_char.keys())]:
                    while random_char in [temp_char['temp'] for temp_char in cor_list if 'temp' in list(temp_char.keys())]:
                        random_char = chr(random.randrange(9632, 9727))
                cor['temp'] = random_char

        # preserve rule ordering with regex, then apply context free changes from largest to smallest
        context_sensitive_rules = [x for x in cor_list if (x['before'] != '' or x['after'] != "")]
        context_free_rules = [x for x in cor_list if x['before'] == "" and x["after"] == ""]
        context_free_rules.sort(key=lambda x: len(x["from"]), reverse=True)
        cor_list = context_sensitive_rules + context_free_rules
        return cor_list
    
    def rule_to_regex(self, rule):
        if rule['before'] is not None:
            before = rule["before"]
        else:
            before = ''
        if rule['after'] is not None:
            after = rule["after"]
        else:
            after = ''
        fromMatch = rule["from"]
        try:
            ruleRX = re.compile(f"(?<={before})" + fromMatch + f"(?={after})")
        except:
            raise Exception('Your regex is malformed. Escape all regular expression special characters in your conversion table.')
        return ruleRX    

    def apply_rules(self, to_parse: str):
        for cor in self.cor_list:
            if re.search(cor["match_pattern"], to_parse):
                # if a temporary value was assigned
                if 'temp' in list(cor.keys()):
                    # turn the original value into the temporary one
                    to_parse = re.sub(cor["match_pattern"], cor["temp"], to_parse)
                else:
                    # else turn it into the final value
                    to_parse = re.sub(cor["match_pattern"], cor["to"], to_parse)
        # transliterate temporary values
        for cor in self.cor_list:
            # transliterate temp value to final value if it exists, otherwise pass
            try:
                if "temp" in cor and cor['temp'] and re.search(cor['temp'], to_parse):
                    to_parse = re.sub(cor['temp'], cor['to'], to_parse)
                else:
                    pass
            except KeyError:
                pass
        return to_parse