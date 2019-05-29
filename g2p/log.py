import coloredlogs, logging
import time
import os

FIELD_STYLES = dict(
    levelname=dict(color='green', bold=coloredlogs.CAN_USE_BOLD_FONT),
)
      
def setup_logger(name):
    logging.basicConfig(
        level=logging.INFO
        # filename="logger.log"
        )
    logger = logging.getLogger(name)
    coloredlogs.install(level='INFO', fmt='%(levelname)s - %(message)s', logger=logger, field_styles=FIELD_STYLES)
    return logger

LOGGER = setup_logger('root')
