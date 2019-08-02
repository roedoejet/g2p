# Gⁱ-2-Pⁱ

[![Coverage Status](https://coveralls.io/repos/github/roedoejet/gi2pi/badge.svg?branch=master)](https://coveralls.io/github/roedoejet/gi2pi?branch=master)
[![Build Status](https://travis-ci.org/roedoejet/gi2pi.svg?branch=master)](https://travis-ci.org/roedoejet/gi2pi)
[![PyPI package](https://img.shields.io/pypi/v/gi2pi.svg)](https://pypi.org/project/gi2pi/)
[![license](https://img.shields.io/github/license/roedoejet/gi2pi.svg)](LICENSE)
[![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg?style=flat-square)](https://github.com/roedoejet/gi2pi)

> Grapheme-to-Phoneme transductions that preserve input and output indices!

This library is for handling arbitrary transductions between input and output segments while preserving indices.

## Table of Contents
- [Gⁱ-2-Pⁱ](#g%e2%81%b1-2-p%e2%81%b1)
  - [Table of Contents](#table-of-contents)
  - [Background](#background)
  - [Install](#install)
  - [Usage](#usage)
    - [Mapping](#mapping)
    - [Transducer](#transducer)
  - [Studio](#studio)
  - [Maintainers](#maintainers)
  - [Contributing](#contributing)
    - [Contributors](#contributors)
  - [License](#license)

## Background

The initial version of this package was developed by [Patrick Littell](https://github.com/littell) and was developed in order to allow for gi2pi from community orthographies to IPA and back again in [ReadAlong-Studio](https://github.com/dhdaines/ReadAlong-Studio). We decided to then pull out the gi2pi mechanism from [Convertextract](https://github.com/roedoejet/convertextract) which allows transducer relations to be declared in CSV files, and turn it into its own library - here it is!

## Install

The best thing to do is install with pip `pip install gi2pi`. 

Otherwise, clone the repo and pip install it locally.

```sh
$ git clone https://github.com/roedoejet/gi2pi.git
$ cd gi2pi
$ pip install -e .
```

## Usage

In order to initialize a `Transducer`, you must first create a `Mapping` object.

### Mapping

You can create mappings either by initializing them directly with a list:

```python
from gi2pi.mappings import Mapping

mappings = Mapping([{"in": 'a', "out": 'b'}])

```

Alternatively, you can add a CSV file to gi2pi/mappings/langs/<YourLang>/<YourLookupTable>

```python
from gi2pi.mappings import Mapping

mappings = Mapping(language={"lang": "<YourLang>", "table": "<YourLookupTable>"})

```

### Transducer

Initialize a `Transducer` with a `Mapping` object. Calling the `Transducer` then produces the output. In order to preserve the indices, pass index=True when calling the `Transducer`.

```python
from gi2pi.mappings import Mapping
from gi2pi.transducer import Transducer

mappings = Mapping([{"in": 'a', "out": 'b'}])
transducer = Transducer(mappings)
transducer('a')
# 'b'
transducer('a', index=True)
# ('b', <gi2pi.transducer.IOStates object>)

```

To make sense of the `IOStates` object that is produced, you can either call it, and produce a list of each character. Doing that for the above produces `[((0, 'a'), (0, 'b'))]` - a list of relation tuples where each relation tuple is comprised of an input and output. Each input tuple and output tuple is in turn comprised of an index and a corresponding character. You can also call `output()` and `input()` to see the plain text output and input respectively.

## Studio

You can also run the `gi2pi Studio` which is a web interface for creating custom lookup tables to be used with gi2pi. To run the `gi2pi Studio` either visit ***** or run it locally using `python run_studio.py`. 

You can also import the app directly from the package:

```python
from gi2pi import app

app.run(host='0.0.0.0', port=5000, debug=True)
```


## Maintainers

[@roedoejet](https://github.com/roedoejet).


## Contributing

Feel free to dive in! [Open an issue](https://github.com/roedoejet/gi2pi/issues/new) or submit PRs.

This repo follows the [Contributor Covenant](http://contributor-covenant.org/version/1/3/0/) Code of Conduct.

### Contributors

This project exists thanks to all the people who contribute. 

[@littell](https://github.com/littell).
[@finguist](https://github.com/finguist).


## License

[MIT](LICENSE) © Aidan Pine
