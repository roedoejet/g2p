#!/bin/sh

# Replace with actual path!
# cmudict.dict is retrievable from https://github.com/cmusphinx/cmudict/blob/master/cmudict.dict
CMUDICT=../../../../../cmudict/cmudict.dict
# Instructions for installing Phonetisaurus are here: https://github.com/AdolfVonKleist/Phonetisaurus
ALIGN=../../../../../Phonetisaurus/phonetisaurus-align

python make_ipa_cmudict.py < $CMUDICT > tmp.txt
$ALIGN --s1_char_delim="" --s2_char_delim="" \
    --seq1_del=true --seq2_del=true --seq1_max=2 --seq2_max=2 \
    --iter=5 --input=tmp.txt --ofile=cmudict.ipa.aligned.txt
rm tmp.txt
