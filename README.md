# Gⁱ-2-Pⁱ

[![Coverage Status](https://coveralls.io/repos/github/roedoejet/g2p/badge.svg?branch=master)](https://coveralls.io/github/roedoejet/g2p?branch=master)
[![Documentation Status](https://readthedocs.org/projects/g2p/badge/?version=latest)](https://g2p.readthedocs.io/en/latest/?badge=latest)
[![Build Status](https://travis-ci.com/roedoejet/g2p.svg?branch=master)](https://travis-ci.com/roedoejet/g2p)
[![PyPI package](https://img.shields.io/pypi/v/g2p.svg)](https://pypi.org/project/g2p/)
[![license](https://img.shields.io/github/license/roedoejet/g2p.svg)](LICENSE)
[![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg?style=flat-square)](https://github.com/roedoejet/g2p)

> Grapheme-to-Phoneme transformations that preserve input and output indices!

This library is for handling arbitrary conversions between input and output segments while preserving indices.

![indices](https://raw.githubusercontent.com/roedoejet/g2p/master/g2p/static/assets/bonjour.png)

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
>>> transducer('hej').output_string
'HH EH Y'
```

There must be a valid path between the `in_lang` and `out_lang` in order for this to work. If you've edited a mapping or added a custom mapping, you must update g2p to include it: `g2p update`

### Writing mapping files

Mapping files are written as either CSV or JSON files. 

#### CSV 

CSV files write each new rule as a new line and consist of at least two columns, and up to four. The first column is required and corresponds to the rule's input. The second column is also
required and corresponds to the rule's output. The third column is optional and corresponds to the context before the rule input. The fourth column is also optional and corresponds to the context after the rule input. For example:

1. This mapping describes two rules; a -> b and c -> d.

```csv
a,b
c,d
```

2. This mapping describes two rules; a -> b / c _ d<sup id="a1">[1](#f1)</sup> and a -> e 

```csv
a,b,c,d
a,e
```

The [g2p studio](https://g2p-studio.herokuapp.com) exports its rules to CSV format.

#### JSON

JSON files are written as an array of objects where each object corresponds to a new rule. The following two examples illustrate how the examples from the CSV section above would be written in JSON:

1. This mapping describes two rules; a -> b and c -> d.

```json
 [
   {
     "in": "a",
     "out": "b"
   },
   {
     "in": "c",
     "out": "d"
   }
 ]
```

2. This mapping describes two rules; a -> b / c _ d<sup id="a1">[1](#f1)</sup>  and a -> e

```json
 [
   {
     "in": "a",
     "out": "b",
     "context_before": "c",
     "context_after": "d"
   },
   {
     "in": "a",
     "out": "e"
   }
 ]
```

## CLI

### `update`

If you edit or add new mappings to the `g2p.mappings.langs` folder, you need to update `g2p`. You do this by running `g2p update`

### `convert`
If you want to convert a string on the command line, you can use `g2p convert <input_text> <in_lang> <out_lang>`
  
Ex. `g2p convert hej dan eng-arpabet` would produce `HH EH Y`

### `generate-mapping`
If your language has a mapping to IPA and you want to generate a mapping between that and the English IPA mapping, you can use `g2p generate-mapping <in_lang> --ipa`.  Remember to run `g2p update` before so that it has the latest mappings for your language.
  
Ex. `g2p generate-mapping dan --ipa` will produce a mapping from `dan-ipa` to `eng-ipa`. You must also run `g2p update` afterwards to update `g2p`. The resulting mapping will be added to the folder in `g2p.mappings.langs.generated`

## Studio

You can also run the `g2p Studio` which is a web interface for creating custom lookup tables to be used with g2p. To run the `g2p Studio` either visit https://g2p-studio.herokuapp.com/ or run it locally using `python run_studio.py`. 

Alternatively, you can run the app from the command line: `g2p run`

## Maintainers

[@roedoejet](https://github.com/roedoejet).


## Contributing

Feel free to dive in! [Open an issue](https://github.com/roedoejet/g2p/issues/new) or submit PRs.

This repo follows the [Contributor Covenant](http://contributor-covenant.org/version/1/3/0/) Code of Conduct.

### Adding a new mapping

In order to add a new mapping, you have to follow the following steps.

1. Determine your language's [ISO 639-3 code](https://en.wikipedia.org/wiki/List_of_ISO_639-3_codes).
2. Add a folder with your language's ISO 639-3 code to `g2p/mappings/langs`
3. Add a configuration file at `g2p/mappings/langs/<yourlangISOcode>/config.yaml`. Here is the basic template for a configuration:

```yaml
<<: &shared
  language_name: <This is the actual name of the language>
mappings:
  - display_name: This is a description of the mapping
    in_lang: This is your language's ISO 639-3 code
    out_lang: This is the output of the mapping
    type: mapping
    authors:
      - <YourNameHere>
    mapping: <FilenameOfMapping>
    <<: *shared
```

4. Add a mapping file. Look at the other mappings for examples, or visit the [g2p studio](https://g2p-studio.herokuapp.com) to practise your mappings.
Mappings are defined in either a CSV or json file. See [writing mapping files](#writing-mapping-files) for more info.
5. After installing your local version (`pip3 install -e .`), update with `g2p update`  
6. Add some tests in `g2p/testspublic/data/<YourIsoCode>.psv`. Each line in the file will run a test with the following structure: `<in_lang>|<out_lang>|<input_string>|<expected_output>`
7. Run `python3 run_tests.py langs` to make sure your tests pass.
8. Make sure you have [checked all the boxes](https://github.com/roedoejet/g2p/blob/master/.github/pull_request_template.md) and make a [pull request]((https://github.com/roedoejet/g2p/pulls)!

### Adding a new language for support with ReadAlongs

This repo is used extensively by [ReadAlongs](https://github.com/ReadAlongs/Studio). In order to make your language supported by ReadAlongs, you must add a mapping from your language's orthography to IPA. So, for example, to add Danish (ISO 639-3: `dan`), the steps above must be followed. The `in_lang` for the mapping must be `dan` and the out_lang must be suffixed with 'ipa' as in `dan-ipa`. The following is the proper configuration:

```yaml
<<: &shared
  language_name: Danish
mappings:
  - display_name: Danish to IPA
    in_lang: dan
    out_lang: dan-ipa
    type: mapping
    authors:
      - Aidan Pine
    mapping: dan_to_ipa.csv
    abbreviations: dan_abbs.csv
    rule_ordering: as-written
    case_sensitive: false
    norm_form: 'none'
    <<: *shared
```

Then, you can generate the mapping between `dan-ipa` and `eng-ipa` by running `g2p generate-mapping --ipa`. This will add the mapping to `g2p/mappings/langs/generated` - do not edit this file, but feel free to have a look. Then, run `g2p update` and submit a [pull request](https://github.com/roedoejet/g2p/pulls), and tada! Your language is supported by ReadAlongs as well!


#### Footnotes

<b id="f1">1</b> If this notation is unfamiliar, have a look at [phonological rewrite rules](https://en.wikipedia.org/wiki/Phonological_rule#:~:text=Phonological%20rules%20are%20commonly%20used,or%20distinctive%20features%20or%20both.) [↩](#a1)


### Contributors

This project exists thanks to all the people who contribute. 

[@littell](https://github.com/littell).
[@finguist](https://github.com/finguist).
[@joanise](https://github.com/joanise).
[@eddieantonio](https://github.com/eddieantonio).
[@dhdaines](https://github.com/dhdaines).


## License

[MIT](LICENSE) © Patrick Littell, Aidan Pine
