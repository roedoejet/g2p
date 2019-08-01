'''
All custom Exceptions
'''

# traceback from exceptions that inherit from this class are suppressed
class CommandLineError(Exception):
    """The traceback of all CommandLineError's is supressed when the
    errors occur on the command line to provide a useful command line
    interface.
    """
    def render(self, msg):
        return msg % vars(self)

class MappingMissing(CommandLineError):
    def __init__(self, language):
        self.language = language['lang']
        self.table = language['table']
    
    def __str__(self):
        return self.render((
            '\n'
            'There is no mapping with the name "%(table)s" for the language "%(language)s", please\n'
            'make sure you spelled the name correctly or go to\n'
            'https://github.com/roedoejet/gi2pi/ for a list of mappings'
        ))

class InvalidNormalization(CommandLineError):
    def __init__(self, norm):
        self.norm = norm
    
    def __str__(self):
        return self.render((
            '\n'
            'You provided an invalid argument "%(norm)s" to normalize with. \n'
            'Please use "none" or "NFC", "NFKC", "NFD", or "NFKD"\n'
        ))

class MalformedMapping(CommandLineError):
    def __init__(self):
        pass
    
    def __str__(self):
        return self.render((
            '\n'
            'You provided a list as your mapping. \n'
            'Not all of the input and output pairs in your mapping have values for "in" and "out"\n'
            'Please fix your mapping.'
        ))

class MalformedLookup(CommandLineError):
    def __init__(self):
        pass
    
    def __str__(self):
        return self.render((
            '\n'
            'In order to use a default lookup table, you need to initialize \n'
            'the Mapping class with a dictionary containing two keys: "lang" and "table". \n'
            'Please try again.'
        ))

class IncorrectFileType(CommandLineError):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.render(self.msg)