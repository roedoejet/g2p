---
comments: true
---

# Python package

## `make_g2p`

The easiest way to create a transducer programmatically is to use the `g2p.make_g2p` function.

To use it, first import the function:

```python
from g2p import make_g2p
```

Then, call it with an argument for `in_lang` and `out_lang`. Both must be strings equal to the name of a particular mapping.

```python
>>> transducer = make_g2p("dan", "eng-arpabet")
>>> transducer("hej").output_string
'HH EH Y'
```

There must be a valid path between the `in_lang` and `out_lang` in order for this to work. If you've edited a mapping or added a custom mapping, you must update g2p to include it: `g2p update`

## `make_tokenizer`

Basic usage for the language-aware tokenizer:

```python
from g2p import make_tokenizer
tokenizer = make_tokenizer("dan")
for token in tokenizer.tokenize_text("Åh, hvordan har du det, Åbenrå?"):
    if token["is_word"]:
        word = token["text"]
    else:
        interword_punctuation_and_spaces = token["text"]
```

Note that selecting the tokenizer language is important to make sure punctuation-like letters are handled correctly. For example `:` and `'` are punctuation in English but they will be part of the word tokens in Kanien'kéha (moh):

```python
>>> list(make_tokenizer("moh").tokenize_text("Kanien'kéha"))
[{'text': "Kanien'kéha", 'is_word': True}]
>>> list(make_tokenizer("eng").tokenize_text("Kanien'kéha"))
[{'text': 'Kanien', 'is_word': True}, {'text': "'", 'is_word': False}, {'text': 'kéha', 'is_word': True}]
```

## A look under the hood

A Mapping object is a list of defined rules. A `Rule` has the following permitted fields:

::: g2p.mappings.Rule
    options:
        show_root_heading: true
        show_source: false
        heading_level: 3
        members_order: source
