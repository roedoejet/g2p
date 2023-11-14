import re

EXPLICIT_INDEX_PATTERN = re.compile(r"{\d+}")


def strip_index_notation(string: str) -> str:
    """Return a string stripped of any explicit indices

    >>> strip_index_notation('test')
    'test'

    >>> strip_index_notation('t{1}e{2}st')
    'test'

    Args:
        string (str): a string that might have explicit indices

    Returns:
        str: a string without explicit indices
    """
    return re.sub(EXPLICIT_INDEX_PATTERN, "", string)
