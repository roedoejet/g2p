"""
Common code to access the data in tests/public/data

Test files (in g2p/tests/public/data) are either .csv, .psv, or .tsv files, the
only difference being the delimiter used (comma, pipe (|), or tab).

Each line in the test file consists of SOURCE,TARGET,INPUT,OUTPUT
"""

import csv
import os
from glob import glob

from g2p.log import LOGGER

"""Directory where the public test data is located"""
DATA_DIR = os.path.dirname(__file__)

"""Cached for langs data, so we don't have to reload it multiple times"""
loaded_langs_to_test = None


def load_public_test_data():
    """Load public/data/*.?sv for test data in various languages

    Returns: List[List[in_lang, out_lang, in_text, out_text]]
    """
    global loaded_langs_to_test
    if loaded_langs_to_test is not None:
        return loaded_langs_to_test

    langs_to_test = []
    for fn in sorted(glob(os.path.join(DATA_DIR, "*.*sv"))):
        if fn.endswith("csv"):
            delimiter = ","
        elif fn.endswith("psv"):
            delimiter = "|"
        elif fn.endswith("tsv"):
            delimiter = "\t"
        with open(fn, encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile, delimiter=delimiter)
            for i, row in enumerate(reader):
                if len(row) == 0 or (len(row) == 1 and row[0].strip() == ""):
                    # skip empty and comment lines
                    continue
                elif row[0][:1] == "#":
                    # skip comments, but check them for stray quotes
                    if "\n" in "".join(row):
                        raise Exception(
                            f"Comment on line {i+1} of {fn} absorbed the next data line(s)."
                            "Please remove stray double quotes."
                        )
                    continue
                elif len(row) < 4:
                    LOGGER.warning(
                        f"Row in {fn} containing values {row} does not have the right values."
                        f"Please check your data."
                    )
                else:
                    langs_to_test.append(row)

    loaded_langs_to_test = langs_to_test
    return langs_to_test
