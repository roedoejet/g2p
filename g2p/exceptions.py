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

class CorrespondenceMissing(CommandLineError):
    def __init__(self, language):
        self.language = language['lang']
        self.table = language['table']
    
    def __str__(self):
        return self.render((
            '\n'
            'There is no correspondence with the name "%(table)s" for the language "%(language)s", please\n'
            'make sure you spelled the name correctly or go to\n'
            'https://github.com/roedoejet/g2p/ for a list of correspondences'
        ))

class MalformedCorrespondence(CommandLineError):
    def __init__(self):
        pass
    
    def __str__(self):
        return self.render((
            '\n'
            'You provided a list as your correspondences. \n'
            'Not all of your correspondences have values for "from" and "to"\n'
            'Please fix your correspondences.'
        ))

class MalformedLookup(CommandLineError):
    def __init__(self):
        pass
    
    def __str__(self):
        return self.render((
            '\n'
            'In order to use a default lookup table, you need to initialize \n'
            'the Correspondence class with a dictionary containing two keys: "lang" and "table". \n'
            'Please try again.'
        ))