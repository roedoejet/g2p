"""

Time how long it takes to initialize panphon.distance.Distance() repeatedly,
and how fast is_panphon() is when using various singleton or non-singleton solutions.

Conclusion:
dst = panphon.distance.Distance() costs about 400ms the first time, about 180ms each
subsequent times.

Using a global constant singleton costs about 0.00015ms per call after the initial 400ms
initialization cost was incurred.

Using hasattr() costs about 0.00022ms per call after the initial 400ms initialization cost
was incurred.

"""

import panphon.distance
from linetimer import CodeTimer

from g2p.mappings import Mapping
from g2p.mappings.langs.utils import is_panphon
from g2p.transducer import Transducer

_PANPHON_DISTANCE_SINGLETON = None


def getPanphonDistanceSingleton1():
    global _PANPHON_DISTANCE_SINGLETON
    if _PANPHON_DISTANCE_SINGLETON is None:
        _PANPHON_DISTANCE_SINGLETON = panphon.distance.Distance()
    return _PANPHON_DISTANCE_SINGLETON


def getPanphonDistanceSingleton2():
    if not hasattr(getPanphonDistanceSingleton2, "value"):
        setattr(getPanphonDistanceSingleton2, "value", panphon.distance.Distance())
    return getPanphonDistanceSingleton2.value


for iters in (1, 1, 10, 100, 1000, 10000):
    with CodeTimer(f"getPanphonDistanceSingleton1() {iters} times"):
        for i in range(iters):
            dst = getPanphonDistanceSingleton1()
    with CodeTimer(f"getPanphonDistanceSingleton2() {iters} times"):
        for i in range(iters):
            dst = getPanphonDistanceSingleton2()

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
            dst = panphon.distance.Distance()

for iters in (1, 10, 100, 1000):
    with CodeTimer(f"Transducer(Mapping(id='panphon_preprocessor')) {iters} times"):
        panphon_preprocessor = Transducer(Mapping(id="panphon_preprocessor"))
