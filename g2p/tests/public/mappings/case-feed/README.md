#### case-feeding mapping

Use case: for spelling conversion where all rules have to prevent feeding of
output text to input text of other rules, but need to allow feeding of output
text to `context_before` or `context_after`.

This three-step mapping:
 - first lowercases the input;
 - then applies the rules from lowercase input to uppercase output, in such a
   way that anything that's been converted cannot be converted again, similar to
   what `prevent_feeding` does, but allowing the context to specify upper and
   lower cases variants to allow both pre- and post-mapping matches;
 - and finally lowercases the output again.

This ends up being equivalent to a case-insensitive prevent-feeding mapping,
except for the behaviour of contexts.
