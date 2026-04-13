import unicodedata


def strip_accents_keep_enye(text):
    """Remove accents while preserving spanish n with tilde (n/N + combining tilde)."""
    if not text:
        return text

    nfd = unicodedata.normalize('NFD', text)
    result = ''.join(
        char for char in nfd
        if unicodedata.category(char) != 'Mn' or char == '\u0303'
    )
    return unicodedata.normalize('NFC', result)
