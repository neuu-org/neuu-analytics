"""
Mapa de abreviacoes dos livros biblicos para nomes completos.
Usado em todas as paginas para exibicao amigavel.
Suporta abreviacoes de ambos os datasets (commentaries + crossrefs).
"""

BOOK_NAMES = {
    # Pentateuco
    "gn": "Genesis",
    "ex": "Exodus",
    "lv": "Leviticus",
    "nm": "Numbers",
    "dt": "Deuteronomy",
    # Historicos
    "jo": "Joshua",
    "jgs": "Judges",
    "ru": "Ruth",
    "1sm": "1 Samuel",
    "2sm": "2 Samuel",
    "1kgs": "1 Kings",
    "2kgs": "2 Kings",
    "1chr": "1 Chronicles",
    "2chr": "2 Chronicles",
    "ezr": "Ezra",
    "neh": "Nehemiah",
    "est": "Esther",
    # Sabedoria
    "jb": "Job",
    "ps": "Psalms",
    "prv": "Proverbs",
    "eccl": "Ecclesiastes",
    "sg": "Song of Songs",
    # Profetas Maiores
    "is": "Isaiah",
    "jer": "Jeremiah",
    "lam": "Lamentations",
    "ez": "Ezekiel",
    "dn": "Daniel",
    # Profetas Menores
    "hos": "Hosea",
    "jl": "Joel",
    "am": "Amos",
    "ob": "Obadiah",
    "jon": "Jonah",
    "mi": "Micah",
    "na": "Nahum",
    "hb": "Habakkuk",
    "zep": "Zephaniah",
    "hg": "Haggai",
    "zec": "Zechariah",
    "mal": "Malachi",
    # Evangelhos
    "mt": "Matthew",
    "mk": "Mark",
    "lk": "Luke",
    "jn": "John",
    # Atos
    "acts": "Acts",
    # Epistolas Paulinas
    "rom": "Romans",
    "1cor": "1 Corinthians",
    "2cor": "2 Corinthians",
    "gal": "Galatians",
    "eph": "Ephesians",
    "phil": "Philippians",
    "col": "Colossians",
    "1thes": "1 Thessalonians",
    "2thes": "2 Thessalonians",
    "1tim": "1 Timothy",
    "2tim": "2 Timothy",
    "tit": "Titus",
    "phlm": "Philemon",
    # Epistolas Gerais
    "heb": "Hebrews",
    "jas": "James",
    "1pet": "1 Peter",
    "2pet": "2 Peter",
    "1jn": "1 John",
    "2jn": "2 John",
    "3jn": "3 John",
    "jude": "Jude",
    # Apocaliptico
    "rev": "Revelation",
}

# Mapa de abreviacoes do crossrefs dataset (formato OSIS) → nome amigavel
CROSSREF_BOOK_NAMES = {
    "GEN": "Genesis", "EXO": "Exodus", "LEV": "Leviticus", "NUM": "Numbers",
    "DEU": "Deuteronomy", "JOS": "Joshua", "JDG": "Judges", "RUT": "Ruth",
    "1SA": "1 Samuel", "2SA": "2 Samuel", "1KI": "1 Kings", "2KI": "2 Kings",
    "1CH": "1 Chronicles", "2CH": "2 Chronicles", "EZR": "Ezra", "NEH": "Nehemiah",
    "EST": "Esther", "JOB": "Job", "PSA": "Psalms", "PRO": "Proverbs",
    "ECC": "Ecclesiastes", "SNG": "Song of Songs", "ISA": "Isaiah", "JER": "Jeremiah",
    "LAM": "Lamentations", "EZE": "Ezekiel", "DAN": "Daniel", "HOS": "Hosea",
    "JOE": "Joel", "AMO": "Amos", "OBA": "Obadiah", "JON": "Jonah",
    "MIC": "Micah", "NAM": "Nahum", "HAB": "Habakkuk", "ZEP": "Zephaniah",
    "HAG": "Haggai", "ZEC": "Zechariah", "MAL": "Malachi",
    "MAT": "Matthew", "MRK": "Mark", "LUK": "Luke", "JHN": "John",
    "ACT": "Acts", "ROM": "Romans", "1CO": "1 Corinthians", "2CO": "2 Corinthians",
    "GAL": "Galatians", "EPH": "Ephesians", "PHP": "Philippians", "COL": "Colossians",
    "1TH": "1 Thessalonians", "2TH": "2 Thessalonians", "1TI": "1 Timothy",
    "2TI": "2 Timothy", "TIT": "Titus", "PHM": "Philemon", "HEB": "Hebrews",
    "JAS": "James", "1PE": "1 Peter", "2PE": "2 Peter", "1JN": "1 John",
    "2JN": "2 John", "3JN": "3 John", "JUD": "Jude", "REV": "Revelation",
}

# Mapa crossref abbrev → commentaries abbrev
CROSSREF_TO_COMM = {
    "GEN": "gn", "EXO": "ex", "LEV": "lv", "NUM": "nm", "DEU": "dt",
    "JOS": "jo", "JDG": "jgs", "RUT": "ru", "1SA": "1sm", "2SA": "2sm",
    "1KI": "1kgs", "2KI": "2kgs", "1CH": "1chr", "2CH": "2chr", "EZR": "ezr",
    "NEH": "neh", "EST": "est", "JOB": "jb", "PSA": "ps", "PRO": "prv",
    "ECC": "eccl", "SNG": "sg", "ISA": "is", "JER": "jer", "LAM": "lam",
    "EZE": "ez", "DAN": "dn", "HOS": "hos", "JOE": "jl", "AMO": "am",
    "OBA": "ob", "JON": "jon", "MIC": "mi", "NAM": "na", "HAB": "hb",
    "ZEP": "zep", "HAG": "hg", "ZEC": "zec", "MAL": "mal",
    "MAT": "mt", "MRK": "mk", "LUK": "lk", "JHN": "jn", "ACT": "acts",
    "ROM": "rom", "1CO": "1cor", "2CO": "2cor", "GAL": "gal", "EPH": "eph",
    "PHP": "phil", "COL": "col", "1TH": "1thes", "2TH": "2thes",
    "1TI": "1tim", "2TI": "2tim", "TIT": "tit", "PHM": "phlm", "HEB": "heb",
    "JAS": "jas", "1PE": "1pet", "2PE": "2pet", "1JN": "1jn", "2JN": "2jn",
    "3JN": "3jn", "JUD": "jude", "REV": "rev",
}

COMM_TO_CROSSREF = {v: k for k, v in CROSSREF_TO_COMM.items()}

# Mapa nome EN → nome PT (para buscar versiculos em traducoes portuguesas)
EN_TO_PT_BOOK = {
    "Genesis": "Gênesis", "Exodus": "Êxodo", "Leviticus": "Levítico",
    "Numbers": "Números", "Deuteronomy": "Deuteronômio", "Joshua": "Josué",
    "Judges": "Juízes", "Ruth": "Rute", "1 Samuel": "1 Samuel", "2 Samuel": "2 Samuel",
    "1 Kings": "1 Reis", "2 Kings": "2 Reis", "1 Chronicles": "1 Crônicas",
    "2 Chronicles": "2 Crônicas", "Ezra": "Esdras", "Nehemiah": "Neemias",
    "Esther": "Ester", "Job": "Jó", "Psalms": "Salmos", "Proverbs": "Provérbios",
    "Ecclesiastes": "Eclesiastes", "Song of Songs": "Cânticos",
    "Isaiah": "Isaías", "Jeremiah": "Jeremias",
    "Lamentations": "Lamentações de Jeremias", "Ezekiel": "Ezequiel",
    "Daniel": "Daniel", "Hosea": "Oséias", "Joel": "Joel", "Amos": "Amós",
    "Obadiah": "Obadias", "Jonah": "Jonas", "Micah": "Miquéias", "Nahum": "Naum",
    "Habakkuk": "Habacuque", "Zephaniah": "Sofonias", "Haggai": "Ageu",
    "Zechariah": "Zacarias", "Malachi": "Malaquias",
    "Matthew": "Mateus", "Mark": "Marcos", "Luke": "Lucas", "John": "João",
    "Acts": "Atos", "Romans": "Romanos", "1 Corinthians": "1 Coríntios",
    "2 Corinthians": "2 Coríntios", "Galatians": "Gálatas", "Ephesians": "Efésios",
    "Philippians": "Filipenses", "Colossians": "Colossenses",
    "1 Thessalonians": "1 Tessalonicenses", "2 Thessalonians": "2 Tessalonicenses",
    "1 Timothy": "1 Timóteo", "2 Timothy": "2 Timóteo", "Titus": "Tito",
    "Philemon": "Filemom", "Hebrews": "Hebreus", "James": "Tiago",
    "1 Peter": "1 Pedro", "2 Peter": "2 Pedro", "1 John": "1 João",
    "2 John": "2 João", "3 John": "3 João", "Jude": "Judas",
    "Revelation": "Apocalipse",
}
PT_TO_EN_BOOK = {v: k for k, v in EN_TO_PT_BOOK.items()}

# Ordem canonica dos livros
BOOK_ORDER = list(BOOK_NAMES.keys())


def friendly_name(abbrev: str) -> str:
    """Retorna o nome amigavel de um livro a partir de qualquer formato de abreviacao."""
    return BOOK_NAMES.get(abbrev, CROSSREF_BOOK_NAMES.get(abbrev, abbrev))


def abbrev_from_name(name: str) -> str:
    """Retorna a abreviacao (commentaries) a partir do nome completo."""
    reverse = {v: k for k, v in BOOK_NAMES.items()}
    return reverse.get(name, name)


def book_name_for_translation(en_name: str, translation: str) -> str:
    """Retorna o nome do livro adequado para a traducao (PT ou EN)."""
    pt_translations = {"ACF", "ARA", "ARC", "AS21", "NAA", "NTLH", "NVI", "NVT"}
    if translation in pt_translations:
        return EN_TO_PT_BOOK.get(en_name, en_name)
    return en_name
