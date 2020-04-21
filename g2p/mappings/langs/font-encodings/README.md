# Font encodings

Before broad utf8 support, communities often resorted to encoding or 'hacking' their characters into a font, and abusing a separate Unicode codepoint to render the character in their writing system as needed. This folder should be where these types of mappings are handled. 

Some style guidelines:
* The `in_lang` key should end with `-font`
* If the mapping is general, please use `Undetermined` as the language name

Currently the following are supported:
* SIL Fonts
    - Heiltsuk Doulos
    - Heiltsuk Times
    - Navajo Times
* [UBC First Nations Unicode Font](https://fnel.arts.ubc.ca/resources/font/)
