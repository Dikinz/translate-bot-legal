"""Соответствие эмодзи-флагов языкам DeepL (target_lang)."""

# Код языка DeepL -> название для отображения
LANGUAGE_NAMES: dict[str, str] = {
    "AR": "арабский",
    "BG": "болгарский",
    "CS": "чешский",
    "DA": "датский",
    "DE": "немецкий",
    "EL": "греческий",
    "EN": "английский",
    "EN-GB": "английский (UK)",
    "EN-US": "английский (US)",
    "ES": "испанский",
    "ET": "эстонский",
    "FI": "финский",
    "FR": "французский",
    "HU": "венгерский",
    "ID": "индонезийский",
    "IT": "итальянский",
    "JA": "японский",
    "KO": "корейский",
    "LT": "литовский",
    "LV": "латышский",
    "NB": "норвежский",
    "NL": "нидерландский",
    "PL": "польский",
    "PT": "португальский",
    "PT-BR": "португальский (BR)",
    "PT-PT": "португальский",
    "RO": "румынский",
    "RU": "русский",
    "SK": "словацкий",
    "SL": "словенский",
    "SV": "шведский",
    "TR": "турецкий",
    "UK": "украинский",
    "ZH": "китайский",
    "ZH-HANS": "китайский (упр.)",
    "ZH-HANT": "китайский (трад.)",
}

# ISO-код страны -> язык DeepL
_COUNTRY_TO_LANG: dict[str, str] = {
    "GB": "EN-GB", "US": "EN-US", "AU": "EN-GB", "CA": "EN-US", "NZ": "EN-GB", "IE": "EN-GB",
    "RU": "RU", "UA": "UK",
    "DE": "DE", "AT": "DE", "CH": "DE",
    "FR": "FR", "BE": "FR",
    "ES": "ES", "MX": "ES", "AR": "ES", "CO": "ES", "CL": "ES",
    "IT": "IT",
    "PT": "PT-PT", "BR": "PT-BR",
    "PL": "PL", "NL": "NL",
    "JP": "JA", "KR": "KO",
    "CN": "ZH-HANS", "TW": "ZH-HANT", "HK": "ZH-HANT",
    "TR": "TR",
    "SE": "SV", "NO": "NB", "DK": "DA", "FI": "FI",
    "CZ": "CS", "SK": "SK", "BG": "BG", "GR": "EL", "HU": "HU", "RO": "RO",
    "EE": "ET", "LV": "LV", "LT": "LT", "SI": "SL",
    "ID": "ID",
    "SA": "AR", "AE": "AR", "EG": "AR",
}


def _flag(country: str) -> str:
    """'RU' -> '🇷🇺' (пара символов Regional Indicator)."""
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in country)


FLAG_TO_LANG: dict[str, str] = {_flag(c): lang for c, lang in _COUNTRY_TO_LANG.items()}


def lang_for_emoji(emoji: str) -> str | None:
    return FLAG_TO_LANG.get(emoji)


def base_lang(code: str) -> str:
    """'EN-GB' -> 'EN', 'ZH-HANS' -> 'ZH'. Нужно для сравнения с detected_source_language."""
    return code.split("-", 1)[0].upper()
