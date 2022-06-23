from .languages import OPDS_TO_PALACE_LANGUAGE, PALACE_TO_OPDS_LANGUAGE
from .genres import GENRES


def palace_language(val):
    if val in OPDS_TO_PALACE_LANGUAGE: return OPDS_TO_PALACE_LANGUAGE[val]
    if val in PALACE_TO_OPDS_LANGUAGE: return val
    return None

def opds_language(val):
    if val in PALACE_TO_OPDS_LANGUAGE: return PALACE_TO_OPDS_LANGUAGE[val]
    if val in OPDS_TO_PALACE_LANGUAGE: return val
    return None

def normalized_genres(val):
	if val in GENRES: return GENRES[val]
	return []
