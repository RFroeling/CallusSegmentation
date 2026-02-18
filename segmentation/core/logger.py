"""Convenience method for configuring logger within scripts. Simply import module and add:

setup_logging()
"""

import logging


def setup_logging(level=logging.INFO):
    """Configure basic logging for scripts and modules.

    Args:
        level (int): Logging level, defaults to :data:`logging.INFO`.
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s: %(message)s",
    )
