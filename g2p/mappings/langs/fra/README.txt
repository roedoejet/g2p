Notes on French g2p by Eric Joanis

French vowels are quite complicated, and I had a hard time figuring out how to
catch even the common cases. I think I managed OK, but we should not consider
my g2p map definitive.

Just one tricky example:
 y  -> /i/
 u  -> /y/
 ou -> /u/
To get this working withoug having a cyclical graph undoing my work, I mapped
u->y first, and then oy->u, making sure that these rules occur *after* the
mapping of oy->/wa/ earlier in the list.

There were a bunch more challenging cases, solved with a best effort here but
not thoroughly tested. Some other temporary changes are done and reset a few
lines lower, e.g., with nasals, so don't be too surprised if you analyze my
rules to find some that don't seem to make sense, at least in isolation.
