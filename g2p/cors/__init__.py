import csv

class Correspondence(object):
    def __init__(self, language):
        # Load workbook, either from correspondence spreadsheets, or user loaded
        this_dir = os.path.dirname(os.path.abspath(__file__))
        if not isinstance(language, type(None)):
            if isinstance(language, list):
                if all('from' in d for d in language) and all('to' in d for d in language):
                    for cor in language:
                        cor["match_pattern"] = self.rule_to_regex(cor)
                    if self.order_as_is:
                        # Add match pattern regular expression
                        self.cor_list = language
                    else:
                        self.cor_list = self.process_intermediate(language)
                else:
                    raise exceptions.MalformedCorrespondence()
            elif language.endswith('csv'):
                self.cor_list = self.load_from_csv(language)
            else:
                if language.endswith('xlsx'):
                    self.cor_list = self.load_from_workbook(language)
                else:
                    try_default = os.path.join(this_dir, "correspondence_spreadsheets", language + '.xlsx')
                    if os.path.exists(try_default):
                        self.cor_list = self.load_from_workbook(try_default)
                    else:
                        raise exceptions.CorrespondenceMissing(language)
        else:
            raise exceptions.CorrespondenceMissing(language)

    def load_from_csv(self, language):
        ws = []
        with open(language, encoding='utf8') as f:
            reader = csv.reader(f)
            for line in reader:
                ws.append(line)
        # Create wordlist
        cor_list = []

        # Loop through rows in worksheet, create if statements for different columns and append Cors to cor_list.
        for entry in ws:
            newCor = {"from": "", "to": "", "before": "", "after": ""}
           
            newCor['from'] = entry[0]
            newCor['to'] = entry[1]
            try:
                newCor['before'] = entry[2]
            except IndexError:
                newCor['before'] = ''

            try:
                newCor['after'] = entry[3]
            except IndexError:
                newCor['after'] = ''
                
            for k in newCor:
                if isinstance(newCor[k], float) or isinstance(newCor[k], int):
                    newCor[k] = str(newCor[k])
        
            cor_list.append(newCor)

        # Add match pattern regular expression
        for cor in cor_list:
            cor["match_pattern"] = self.rule_to_regex(cor)

        if self.order_as_is:
            return cor_list
        else:
            return self.process_intermediate(cor_list)

    def load_from_workbook(self, language):
        wb = load_workbook(language)
        ws = wb.active
        # Create wordlist
        cor_list = []

        # Loop through rows in worksheet, create if statements for different columns and append Cors to cor_list.
        for entry in ws:
            newCor = {"from": "", "to": "", "before": "", "after": ""}
            for col in entry:
                if col.column == 'A':
                    value = col.value
                    if type(value) == float or int:
                        value = str(value)
                    newCor["from"] = value
                if col.column == 'B':
                    value = col.value
                    if type(value) == float or int:
                        value = str(value)
                    newCor["to"] = value
                if col.column == 'C':
                    if col.value is not None:
                        value = col.value
                        if type(value) == float or int:
                            value = str(value)
                        newCor["before"] = value
                if col.column == 'D':
                    if col.value is not None:
                        value = col.value
                        if type(value) == float or int:
                            value = str(value)
                        newCor["after"] = value
            cor_list.append(newCor)

        # Add match pattern regular expression
        for cor in cor_list:
            cor["match_pattern"] = self.rule_to_regex(cor)

        if self.order_as_is:
            return cor_list
        else:
            return self.process_intermediate(cor_list)

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

    def apply_rules(self, to_parse):
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
