#!/bin/sh

# Replace with actual path!
# cmudict.dict is retrievable from https://github.com/cmusphinx/cmudict/blob/master/cmudict.dict
CMUDICT=../../../../../cmudict/cmudict.dict
# Install Phonetisaurus with `pip install phonetisaurus`
export PATH=$(python -c 'import phonetisaurus as p; print(p.guess_environment()["PATH"])')
export LD_LIBRARY_PATH=$(python -c 'import phonetisaurus as p; print(p.guess_environment()["LD_LIBRARY_PATH"])')

python make_ipa_cmudict.py < $CMUDICT > tmp.txt
phonetisaurus-align --s1_char_delim="" --s2_char_delim="" \
    --seq1_del=true --seq2_del=true --seq1_max=2 --seq2_max=2 \
    --iter=5 --input=tmp.txt --ofile=cmudict.ipa.aligned.txt
rm tmp.txt
