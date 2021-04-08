""" Time how long it takes to initialize panphon.distance.Distance() repeatedly,
    and how fast is_panphon() is when using various singleton or non-singleton solutions.
    (To benchmark the different solutions, I changed mappings.langs.utils.is_panphon and
    reran this timing script.)
"""

from linetimer import CodeTimer
from panphon import distance
from g2p.mappings.langs.utils import is_panphon, getPanphonDistanceSingleton

for iters in (1, 1, 10, 100, 1000, 10000):
    with CodeTimer(f"getPanphonDistanceSingleton() {iters} times"):
        for i in range(iters):
            dst = getPanphonDistanceSingleton()

for words in (1, 10):
    with CodeTimer(f"is_panphon() {words} words"):
        string = " ".join(["ei" for i in range(words)])
        is_panphon(string)

    with CodeTimer(f"is_panphon() on 1 word {words} times"):
        string = "ei"
        for i in range(words):
            is_panphon(string)

for iters in (1, 10):
    with CodeTimer(f"dst init {iters} times"):
        for i in range(iters):
            dst = distance.Distance()
