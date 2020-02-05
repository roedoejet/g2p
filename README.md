# Gⁱ-2-Pⁱ

[![Coverage Status](https://coveralls.io/repos/github/roedoejet/g2p/badge.svg?branch=master)](https://coveralls.io/github/roedoejet/g2p?branch=master)
[![Documentation Status](https://readthedocs.org/projects/g2p/badge/?version=latest)](https://g2p.readthedocs.io/en/latest/?badge=latest)
[![Build Status](https://travis-ci.org/roedoejet/g2p.svg?branch=master)](https://travis-ci.org/roedoejet/g2p)
[![PyPI package](https://img.shields.io/pypi/v/g2p.svg)](https://pypi.org/project/g2p/)
[![license](https://img.shields.io/github/license/roedoejet/g2p.svg)](LICENSE)
[![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg?style=flat-square)](https://github.com/roedoejet/g2p)

> Grapheme-to-Phoneme transductions that preserve input and output indices!

This library is for handling arbitrary transductions between input and output segments while preserving indices.

:warning: :construction: This repo is currently **under construction** :construction: :warning:

It is certainly useable, but you should proceed with caution when integrating into other projects as it is currently pre-alpha and breaking changes should be expected.

## Table of Contents
- [Gⁱ-2-Pⁱ](#g%e2%81%b1-2-p%e2%81%b1)
  - [Table of Contents](#table-of-contents)
  - [Background](#background)
  - [Install](#install)
  - [Usage](#usage)
  - [CLI](#cli)
    - [`update`](#update)
    - [`convert`](#convert)
    - [`generate-mapping`](#generate-mapping)
  - [Studio](#studio)
  - [Maintainers](#maintainers)
  - [Contributing](#contributing)
    - [Contributors](#contributors)
  - [License](#license)

## Background

The initial version of this package was developed by [Patrick Littell](https://github.com/littell) and was developed in order to allow for g2p from community orthographies to IPA and back again in [ReadAlong-Studio](https://github.com/dhdaines/ReadAlong-Studio). We decided to then pull out the g2p mechanism from [Convertextract](https://github.com/roedoejet/convertextract) which allows transducer relations to be declared in CSV files, and turn it into its own library - here it is!

## Install

The best thing to do is install with pip `pip install g2p`. 

Otherwise, clone the repo and pip install it locally.

```sh
$ git clone https://github.com/roedoejet/g2p.git
$ cd g2p
$ pip install -e .
```

## Usage

The easiest way to create a transducer is to use the `g2p.make_g2p` function.

To use it, first import the function:

`from g2p import make_g2p`

Then, call it with an argument for `in_lang` and `out_lang`. Both must be strings equal to the name of a particular mapping.

```python
>>> transducer = make_g2p('dan', 'eng-arpabet')
>>> transducer('hej')
'HH EH Y'
```

There must be a valid path between the `in_lang` and `out_lang` in order for this to work. If you've edited a mapping or added a custom mapping, you must update g2p to include it: `g2p update`

## CLI

### `update`

If you edit or add new mappings to the `g2p.mappings.langs` folder, you need to update `g2p`. You do this by running `g2p update`

### `convert`
If you want to convert a string on the command line, you can use `g2p convert <input_text> <in_lang> <out_lang>`
  
Ex. `g2p convert hej dan eng-arpabet` would produce `HH EH Y`

### `generate-mapping`
If your language has a mapping to IPA and you want to generate a mapping between that and the English IPA mapping, you can use `g2p generate-mapping <in_lang> --ipa`
  
Ex. `g2p generate-mapping dan --ipa` will produce a mapping from `dan-ipa` to `eng-ipa`. You must run `g2p update` afterwards to update `g2p`. The resulting mapping will be added to the folder in `g2p.mappings.langs.generated`

## Studio

You can also run the `g2p Studio` which is a web interface for creating custom lookup tables to be used with g2p. To run the `g2p Studio` either visit https://g2p-studio.herokuapp.com/ or run it locally using `python run_studio.py`. 

Alternatively, you can run the app from the command line: `g2p run`.

## Maintainers

[@roedoejet](https://github.com/roedoejet).


## Contributing

Feel free to dive in! [Open an issue](https://github.com/roedoejet/g2p/issues/new) or submit PRs.

This repo follows the [Contributor Covenant](http://contributor-covenant.org/version/1/3/0/) Code of Conduct.

### Contributors

This project exists thanks to all the people who contribute. 

[@littell](https://github.com/littell).
[@finguist](https://github.com/finguist).
[@joanise](https://github.com/joanise).
[@eddieantonio](https://github.com/eddieantonio).
[@dhdaines](https://github.com/dhdaines).


## License

[MIT](LICENSE) © Patrick Littell, Aidan Pine
