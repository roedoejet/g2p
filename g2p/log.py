"""
    Error Log

"""

import logging

import coloredlogs

FIELD_STYLES = dict(
    levelname=dict(color="green"),
)


def setup_logger(name):
    """Create logger and configure with cool colors!"""

    logger = logging.getLogger(name)
    coloredlogs.install(
        level="INFO",
        fmt="%(levelname)s - %(message)s",
        logger=logger,
        field_styles=FIELD_STYLES,
    )
    return logger


LOGGER = setup_logger("root")
