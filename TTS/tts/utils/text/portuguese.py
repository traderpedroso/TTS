import re
from num2words import num2words


def split_sentence(text, min_len=10):
    text = re.sub("[。！？；]", ".", text)
    text = re.sub("[，]", ",", text)
    text = re.sub("[“”]", '"', text)
    text = re.sub("[‘’]", "'", text)
    text = re.sub(r"[\<\>\(\)\[\]\"\«\»]+", "", text)
    return [item.strip() for item in txtsplit(text, 256, 512) if item.strip()]


def merge_short_sentences(sens):
    sens_out = []
    for s in sens:
        if len(sens_out) > 0 and len(sens_out[-1].split(" ")) <= 2:
            sens_out[-1] = sens_out[-1] + " " + s
        else:
            sens_out.append(s)
    try:
        if len(sens_out[-1].split(" ")) <= 2:
            sens_out[-2] = sens_out[-2] + " " + sens_out[-1]
            sens_out.pop(-1)
    except:
        pass
    return sens_out


def txtsplit(text, desired_length=100, max_length=200):
    text = re.sub(r"\n\n+", "\n", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r'[""]', '"', text)
    text = re.sub(r"([,.?!])", r"\1 ", text)
    text = re.sub(r"\s+", " ", text)

    rv = []
    in_quote = False
    current = ""
    split_pos = []
    pos = -1
    end_pos = len(text) - 1

    def seek(delta):
        nonlocal pos, in_quote, current
        is_neg = delta < 0
        for _ in range(abs(delta)):
            if is_neg:
                pos -= 1
                current = current[:-1]
            else:
                pos += 1
                current += text[pos]
            if text[pos] == '"':
                in_quote = not in_quote
        return text[pos]

    def peek(delta):
        p = pos + delta
        return text[p] if p < end_pos and p >= 0 else ""

    def commit():
        nonlocal rv, current, split_pos
        rv.append(current)
        current = ""
        split_pos = []

    while pos < end_pos:
        c = seek(1)
        if len(current) >= max_length:
            if len(split_pos) > 0 and len(current) > (desired_length / 2):
                d = pos - split_pos[-1]
                seek(-d)
            else:
                while c not in "!?.\n " and pos > 0 and len(current) > desired_length:
                    c = seek(-1)
            commit()
        elif not in_quote and (c in "!?\n" or (c in ".," and peek(1) in "\n ")):
            while pos < len(text) - 1 and len(current) < max_length and peek(1) in "!?.":
                c = seek(1)
            split_pos.append(pos)
            if len(current) >= desired_length:
                commit()
        elif in_quote and peek(1) == '"' and peek(2) in "\n ":
            seek(2)
            split_pos.append(pos)
    rv.append(current)
    rv = [s.strip() for s in rv]
    rv = [s for s in rv if len(s) > 0 and not re.match(r"^[\s\.,;:!?]*$", s)]
    return rv


def normalizer(text):
    text = _normalize_percentages(text)
    text = _normalize_time(text)
    text = _normalize_money(text)
    text = _normalize_am_pm_times(text)
    text = _normalize_numbers_with_letters(text)
    text = _normalize_numbers(text)
    text = _normalize_abbreviations(text)
    text = replace_punctuation(text)
    text = remove_aux_symbols(text)
    text = remove_punctuation_at_begin(text)
    text = collapse_whitespace(text)
    text = re.sub(r"([^\.,!\?\-…])$", r"\1.", text)
    text = re.sub(r"(?<!\.)\.(?!\.)", ";", text)
    text = re.sub(r"\.\.+", "...", text)  # Corrige a substituição excessiva de pontos
    return text


def save_to_txt(file_path, content):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            existing_content = file.readlines()

        if f"{content}\n" in existing_content:
            pass
        else:
            with open(file_path, "a", encoding="utf-8") as file:
                file.write(f"{content}\n")
            print(f"Conteúdo '{content}' adicionado com sucesso.")
    except FileNotFoundError:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(f"{content}\n")
        print(f"Arquivo criado e conteúdo '{content}' adicionado com sucesso.")


def process_train_list(file_path, text_cleaner):
    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    second_column_texts = [line.split("|")[1].strip() for line in lines]

    for text in second_column_texts:
        text_cleaner(text)


_whitespace_re = re.compile(r"\s+")

rep_map = {
    "：": ",",
    "；": ",",
    "，": ",",
    "。": ".",
    "！": "!",
    "？": "?",
    "\n": ".",
    "·": ",",
    "、": ",",
    "...": "...",  # Corrige a substituição excessiva de ...
    "…": "...",
    "$": ".",
    "“": "'",
    "”": "'",
    "‘": "'",
    "’": "'",
    "（": "'",
    "）": "'",
    "(": "'",
    ")": "'",
    "《": "'",
    "》": "'",
    "【": "'",
    "】": "'",
    "[": "'",
    "]": "'",
    "—": "",
    "～": "-",
    "~": "-",
    "「": "'",
    "」": "'",
    "& ": " e ",
}


abbreviations = [
    (re.compile(r"\b%s\b" % re.escape(x[0]), re.IGNORECASE), x[1])
    for x in [
        ("sr", "senhor"),
        ("sra", "senhora"),
        ("dr", "doutor"),
        ("dra", "doutora"),
        ("prof", "professor"),
        ("eng", "engenheiro"),
        ("ltda", "limitada"),
        ("adv", "advogado"),
        ("etc.", "etcetera"),
        ("kb", "kilobyte"),
        ("gb", "gigabyte"),
        ("mb", "megabyte"),
        ("kw", "quilowatt"),
        ("mw", "megawatt"),
        ("gw", "gigawatt"),
        ("kg", "quilograma"),
        ("hz", "hertz"),
        ("khz", "quilo-hertz"),
        ("mhz", "mega-hertz"),
        ("ghz", "giga-hertz"),
        ("km", "quilômetro"),
        ("ltda", "limitada"),
        ("jan", "janeiro"),
        ("fev", "fevereiro"),
        ("mar", "março"),
        ("abr", "abril"),
        ("mai", "maio"),
        ("jun", "junho"),
        ("jul", "julho"),
        ("ago", "agosto"),
        ("set", "setembro"),
        ("out", "outubro"),
        ("nov", "novembro"),
        ("dez", "dezembro"),
        ("pág", "página"),
        ("págs", "páginas"),
        ("s.a", "sociedade anônima"),
        ("cia", "companhia"),
        ("etc", "et cetera"),
    ]
]


def replace_punctuation(text):
    pattern = re.compile("|".join(re.escape(p) for p in rep_map.keys()))
    replaced_text = pattern.sub(lambda x: rep_map[x.group()], text)
    return replaced_text


def lowercase(text):
    return text.lower()


def collapse_whitespace(text):
    return re.sub(_whitespace_re, " ", text).strip()


def remove_punctuation_at_begin(text):
    return re.sub(r"^[,.!?]+", "", text)


def remove_aux_symbols(text):
    text = re.sub(r"[\<\>\(\)\[\]\"\«\»\']+", "", text)
    return text


def _normalize_percentages(text):
    return re.sub(r"(\d+)%", lambda m: num2words(m.group(1), lang="pt") + " por cento", text)


def _normalize_time(text):
    def time_to_words(match):
        hours = int(match.group(1))
        minutes = int(match.group(2))
        hours_text = num2words(hours, lang="pt", to="cardinal")
        if minutes == 0:
            return f"{hours_text} hora" + ("s" if hours > 1 else "")
        minutes_text = num2words(minutes, lang="pt", to="cardinal")
        return (
            f"{hours_text} hora"
            + ("s" if hours > 1 else "")
            + f" e {minutes_text} minuto"
            + ("s" if minutes > 1 else "")
        )

    return re.sub(r"(\d{1,2}):(\d{2})", time_to_words, text)


def _normalize_money(text):
    def money_to_words_millions(match):
        currency = match.group(1)
        integer_part = match.group(2).replace(".", "")
        suffix = match.group(3)

        amount_text = num2words(int(integer_part), lang="pt")
        return f"{amount_text} {suffix} de reais"

    def money_to_words_cents(match):
        currency = match.group(1)
        integer_part = match.group(2).replace(".", "")
        decimal_part = match.group(3)

        integer_amount_text = num2words(int(integer_part), lang="pt")
        decimal_amount_text = num2words(int(decimal_part), lang="pt")
        return f"{integer_amount_text} reais e {decimal_amount_text} centavos"

    def money_to_words_integers(match):
        currency = match.group(1)
        integer_part = match.group(2).replace(".", "")

        amount = int(integer_part)
        amount_text = num2words(amount, lang="pt")

        if amount > 1:
            currency_text = "reais"
        else:
            currency_text = "real"

        return f"{amount_text} {currency_text}"

    text = re.sub(r"(R\$|€|£|\$) (\d+)( milhões| bilhões)", money_to_words_millions, text)
    text = re.sub(r"(R\$|€|£|\$)(\d+)( milhões| bilhões)", money_to_words_millions, text)
    text = re.sub(r"(R\$|€|£|\$) (\d+),(\d{2})", money_to_words_cents, text)
    text = re.sub(r"(R\$|€|£|\$)(\d+),(\d{2})", money_to_words_cents, text)
    text = re.sub(r"(R\$|€|£|\$) (\d+)", money_to_words_integers, text)
    text = re.sub(r"(R\$|€|£|\$)(\d+)", money_to_words_integers, text)

    return text


def _normalize_numbers(text):
    return re.sub(r"\b\d+\b", lambda x: num2words(x.group(), lang="pt"), text)


def _normalize_abbreviations(text):
    for regex, substitution in abbreviations:
        text = regex.sub(substitution, text)
    return text


def _normalize_am_pm_times(text):
    def am_pm_to_words(match):
        hours = int(match.group(1))
        period = match.group(2).lower()
        if period == "pm" and hours != 12:
            hours += 12
        elif period == "am" and hours == 12:
            hours = 0
        hours_text = num2words(hours, lang="pt", to="cardinal")
        return f"{hours_text} horas"

    return re.sub(r"(\d{1,2})(am|pm)", am_pm_to_words, text)


def _normalize_numbers_with_letters(text):
    return re.sub(
        r"(\d+)([a-zA-Z]+)",
        lambda m: f"{num2words(m.group(1), lang='pt')} {m.group(2)}",
        text,
    )
