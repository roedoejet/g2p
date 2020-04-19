Language-specific files for Northern East Cree

AP: There seems to be a problem here with normalization. Most of the rules for long vowels are declared with \u1427 "canadian syllabics final middle dot", so ᐧᐋ is a sequence of \u1427\140B, but there also appears to be a specific code point for waa: \u1419. I've added a crl_norm.json that normalizes the sequence to the single codepoint for that character and changed the crl_to_ipa.json mapping to use \u1419 instead of \u1427\140B, but I'm not sure if this was the right choice. Either way, there needs to be some sort of normalization step here to handle real world input.


DT: I have fixed the mappings so that all the w syllables are using the one unicode character instead of the two unicode sequence ( \u1427 plus unicode character). 
