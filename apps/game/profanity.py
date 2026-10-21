import unicodedata

_LEET_MAP = str.maketrans({"4": "a", "3": "e", "1": "i", "0": "o", "5": "s", "7": "t", "@": "a"})

BLOCKED_WORDS = {
    # Türkçe
    "amk", "amq", "siktir", "sik", "yarrak", "oç", "pic", "piç", "orospu",
    "yavsak", "yavşak", "gocuk", "ibne", "göt", "got", "surtuk", "sürtük",
    # English
    "fuck", "shit", "bitch", "asshole", "bastard", "cunt", "dick", "nigger",
    "whore", "slut",
}


def _normalize(value):
    value = value.casefold().translate(_LEET_MAP)
    value = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in value if ch.isalnum())


def contains_profanity(name):
    normalized = _normalize(name)
    return any(word in normalized for word in BLOCKED_WORDS)
