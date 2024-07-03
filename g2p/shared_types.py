"""
This file is for abstract type definitions that can be initialized without any
(expensive) dependencies.
"""

from abc import ABC, abstractmethod


class BaseTransducer(ABC):
    """Base class to typecheck transducers without having to import them."""

    @abstractmethod
    def __call__(self, to_convert: str):
        """Transduce to_convert."""


class BaseTransductionGraph(ABC):
    """Base class to typecheck transduction graphs without having to import them."""

    @property
    @abstractmethod
    def tiers(self):
        """A list of BaseTransductionGraph objects for each tier in the graph."""


class BaseTokenizer(ABC):
    """Base class to typecheck tokenizers without having to import them."""

    @abstractmethod
    def tokenize_text(self, text):
        """Tokenize text."""
