"""
    Error Log

"""

import logging
import coloredlogs
import sys

FIELD_STYLES = dict(
    levelname=dict(color='green', bold=coloredlogs.CAN_USE_BOLD_FONT),
)

def setup_logger(name):
    """ Create logger and configure with cool colors!
    """

    logging.basicConfig(
        level=logging.INFO
        # filename="logger.log"
    )
    logger = logging.getLogger(name)
    coloredlogs.install(level='INFO', fmt='%(levelname)s - %(message)s',
                        logger=logger, field_styles=FIELD_STYLES)
    return logger

class LogCounter:
    ''' A wrapper for the logger to determine how many times
        an error is logged
    '''
    def __init__(self, fn):
        self.fn = fn
        self.count = 0
    
    def __call__(self, *args, **kwargs):
        self.count += 1
        return self.fn(*args, **kwargs)

LOGGER = setup_logger('root')

TEST_LOGGER = setup_logger('test')

FH = logging.FileHandler('test.log')

TEST_LOGGER.addHandler(FH)
