"""
This file is for abstract type definitions that can be initialized without any
(expensive) dependencies.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from typing_extensions import deprecated


@dataclass
class Token:
    """A token from the g2p tokenizer."""

    text: str
    is_word: bool

    @deprecated(
        "Accessing g2p Token objects as dicts is deprecated since g2p 2.2.0. "
        "Please use the 'text' and 'is_word' attributes instead.",
    )
    def __getitem__(self, key):
        """For backward compatibility only, allow access as if it were a dict."""
        if key == "text":
            return self.text
        if key == "is_word":
            return self.is_word
        raise KeyError(key)

    @deprecated(
        "Accessing g2p Token objects as dicts is deprecated since g2p 2.2.0. "
        "Please use the 'text' and 'is_word' attributes instead.",
    )
    def __setitem__(self, key, value):
        """For backward compatibility only, allow setting values as if it were a dict."""
        if key == "text":
            self.text = value
        elif key == "is_word":
            self.is_word = value
        else:
            raise KeyError(key)


class BaseTransducer(ABC):
    """Base class to typecheck transducers without having to import them."""

    @abstractmethod
    def __call__(self, to_convert: str):
        """Transduce to_convert."""

    @property
    @abstractmethod
    def transducers(self):
        """A list of BaseTransducer objects for each tier in the transducer."""

    @property
    @abstractmethod
    def in_lang(self) -> str:
        """The input language code of the transducer."""

    @property
    @abstractmethod
    def out_lang(self) -> str:
        """The output language code of the transducer."""


class BaseTransductionGraph(ABC):
    """Base class to typecheck transduction graphs without having to import them."""

    @property
    @abstractmethod
    def tiers(self):
        """A list of BaseTransductionGraph objects for each tier in the graph."""


class BaseTokenizer(ABC):
    """Base class to typecheck tokenizers without having to import them."""

    @abstractmethod
    def tokenize_text(self, text: str) -> List[Token]:
        """Tokenize text."""
