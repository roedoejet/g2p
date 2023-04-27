"""Hide deprecation and version checking code here so it's not in the way.

Usage: g2p.__init__ should simply do "import g2p.deprecation" in order to get the Python
version validated. Other functions can be added and invoked as needed.
"""

import sys

from g2p.log import LOGGER
import g2p._version

if sys.version_info < (3, 6):  # pragma: no cover
    sys.exit(
        f"Python 3.6 or more recent is required by g2p. You are using {sys.version}.\n"
        "Please use a newer version of Python."
    )


def handle_tok_lang_deprecation(tok_lang):
    """Warn or raise about using the deprecated tok_lang arg to make_g2p"""
    if tok_lang:
        if g2p._version.VERSION < "2.0":
            LOGGER.warning(
                "Deprecation warning: the tok_lang argument to make_g2p is deprecated, "
                "and will be removed in g2p version 2.0 "
                "Use tokenize=True or create a custom_tokenizer using make_tokenizer() instead."
            )
        else:
            raise TypeError(
                "Deprecation error: the tok_lang argument to make_g2p has been removed. "
                "Use tokenize=True or create a custom_tokenizer using make_tokenizer() instead."
            )
