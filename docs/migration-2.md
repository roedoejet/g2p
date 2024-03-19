---
comments: true
---

# Migrating from `g2p` 1.0

The `g2p` 2.0 release introduces a number of improvements and changes
which, unfortunately, are incompatible with mappings and Python code
written for the previous version.  We have tried to describe them here
with the changes you will need to make to your code and data.

## Mapping configurations have changed (for the better)

The configurations for mappings (which you'll find in
`g2p/mappings/langs/*/config-g2p.yaml`) are now validated with a [YAML
Schema](https://raw.githubusercontent.com/roedoejet/g2p/main/g2p/mappings/.schema/g2p-config-schema-2.0.json).
If you use an editor like [Visual Studio
Code](https://code.visualstudio.com/), the names of fields will be
autocompleted and some warnings will be shown for possible values.
This also works with GNU Emacs using
[lsp-mode](https://emacs-lsp.github.io/lsp-mode/) and probably other
editors.

In order for this magic to work, we needed to give the configuration
files a somewhat more meaningful name than `config.yaml`, so they must
now be called `config-g2p.yaml`.  In addition some fields have changed
names to reflect the fact that they refer to *files* and not the
actual rules themselves:

- `mapping` is now `rules_path`
- `abbreviations` is now `abbreviations_path`

The mappings themselves should be compatible with the previous
version, please let us know if you encounter any problems.

## Submodules of `g2p` must be imported explicitly

Previously, when you called `import g2p`, it imported absolutely
everything, which caused the command-line interface (and probably your
program too) to start up very, very slowly.

If you simply use the public and documented `make_g2p` API, this will
not change anything, but if you relied on internal classes and
functions from `g2p.mappings`, `g2p.transducer`, etc, then you can no
longer depend on them being also accessible in the top-level `g2p`
package.  For example, you will need to make this sort of change:

```diff
- from g2p import Mapping, Transducer, make_tokenizer
+ from g2p.mappings import Mapping
+ from g2p.transducer import Transducer
+ from g2p.mappings.tokenizer import make_tokenizer
```

**NOTE** These are not public APIs, and are subject to further
changes.  This guide is provided as a courtesy to anyone who may have
been using them and should not be construed as public API documentation.

## Mappings and rules use properties to access their fields

Along the same lines, access to the internal structure of rule-based
mappings has changed considerably (and for the better) due to the use
of [Pydantic](https://docs.pydantic.dev/latest/).  This means,
however, that you can no longer treat them as the simple dictionaries
that they used to be, since they are no longer that.  Instead, use
properties, which correspond to the names used in `config-g2p.yaml`.

For example, you can access the `case_sensitive` flag using the
property of the same name (note also that you can no longer construct
a `Mapping` by simply passing the name of the file):

```python
mapping = Mapping.load_from_file("path/to/some/config-g2p.yaml")
print("Case sensitive?", mapping.case_sensitive)
```

To iterate over the rules in a mapping, you now use the `rules`
property instead of the `mapping_data` field.  The rules themselves
now also use properties for access, which do not entirely correspond
to the names used in the JSON definition, because `in`, for example,
is a reserved word in Python.  So for instance you would make this
change:

```diff
- for rule in mapping["mapping_data"]:
-     print("Rule maps", rule["in"], "to", rule["out"])
+ for rule in mapping.rules:
+     print("Rule maps", rule.rule_input, "to", rule.rule_output)
```

**NOTE** These are not public APIs, and are subject to further
changes.  This guide is provided as a courtesy to anyone who may have
been using them and should not be construed as public API documentation.

## Some CLI commands no longer exist

Several commands for the `g2p` command-line have been removed as they
were duplicates of other functionality:

- run
- routes
- shell
