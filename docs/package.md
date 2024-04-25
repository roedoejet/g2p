---
comments: true
---

# Python package

The easiest way to create a transducer programmatically is to use the `g2p.make_g2p` function.

To use it, first import the function:

```python
from g2p import make_g2p
```

Then, call it with an argument for `in_lang` and `out_lang`. Both must be strings equal to the name of a particular mapping.

```python
>>> transducer = make_g2p('dan', 'eng-arpabet')
>>> transducer('hej').output_string
'HH EH Y'
```

There must be a valid path between the `in_lang` and `out_lang` in order for this to work. If you've edited a mapping or added a custom mapping, you must update g2p to include it: `g2p update`

## A look under the hood

A Mapping object is a list of defined rules.

::: g2p.mappings.Mapping
    options:
        show_root_heading: true
        show_source: false
        heading_level: 4

A Transducer object is initialized with a Mapping object and when called, applies each rule of the Mapping in sequence
on the input to produce the resulting output.

::: g2p.transducer.Transducer
    options:
        show_root_heading: true
        show_source: false
        heading_level: 4
