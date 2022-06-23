# Springer map to ISO-639-2 (B)
# taken from ThePalaceProject/circulation/core/util/languages
OPDS_TO_PALACE_LANGUAGE = {
    "de": "ger",
    "en": "eng",
    "es": "spa",
    "fr": "fre",
    "it": "ita",
    "nl": "dut",
    "pl": "pol",
    "pt": "por",
    "zh": "chi",
}

PALACE_TO_OPDS_LANGUAGE = dict((item[1], item[0]) for item in OPDS_TO_PALACE_LANGUAGE.items())
