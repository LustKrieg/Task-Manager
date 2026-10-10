from datetime import datetime


_language = "English"
SUPPORTED_LANGUAGES = ("English", "Русский")

_TRANSLATIONS = {
    "Task Manager": "Менеджер Задач",
    "Settings": "Настройки",
    "Preferences": "Настройки",
    "Active": "Активные",
    "Completed": "Выполненные",
    "Recently Deleted": "Недавно удалённые",
    "Trash": "Корзина",
    "Search": "Поиск",
    "Restore": "Восстановить",
    "Delete Forever": "Удалить навсегда",
    "Restore All": "Восстановить все",
    "Delete All": "Удалить все",
    "Delete": "Удалить",
    "Back to tasks": "Назад к задачам",
    "Choose language": "Выбрать язык",
    "Language": "Язык",
    "General": "Основные",
    "Notes": "Заметки",
    "Add Date": "Добавить дату",
    "Add Time": "Добавить время",
    "New Reminder": "Новое напоминание",
    "Created": "Создано",
    "Overdue": "Просрочено",
    "Today": "Сегодня",
    "Tomorrow": "Завтра",
    "No Due Date": "Без срока",
    "English": "English",
    "Русский": "Русский",
}


def available_languages():
    return SUPPORTED_LANGUAGES

_MONTHS_EN = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)
_MONTHS_RU = (
    "январь", "февраль", "март", "апрель", "май", "июнь",
    "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь",
)
_MONTHS_RU_GENITIVE = (
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
)
_MONTHS_RU_ABBREVIATED = (
    "янв.", "фев.", "мар.", "апр.", "мая", "июн.",
    "июл.", "авг.", "сен.", "окт.", "ноя.", "дек.",
)
_WEEKDAYS_EN = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
_WEEKDAYS_RU = ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")


def set_language(language):
    global _language
    _language = "Русский" if language == "Русский" else "English"


def current_language():
    return _language


def is_russian():
    return _language == "Русский"


def tr(text):
    if is_russian():
        return _TRANSLATIONS.get(text, text)
    return text


def month_abbreviations():
    if is_russian():
        return list(_MONTHS_RU_ABBREVIATED)
    return ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def weekday_abbreviations(first_day=1):
    names = _WEEKDAYS_RU if is_russian() else _WEEKDAYS_EN
    start = (first_day - 1) % 7
    return list(names[start:] + names[:start])


def calendar_month(year, month):
    if is_russian():
        return f"{_MONTHS_RU[month - 1]} {year}"
    return datetime(year, month, 1).strftime("%b %Y")


def format_due_datetime(value):
    if value is None:
        return ""
    if is_russian():
        return f"{value.day} {_MONTHS_RU_ABBREVIATED[value.month - 1]} {value:%H:%M}"
    try:
        return value.strftime("%b %-d, %-I:%M %p")
    except ValueError:
        return value.strftime("%b %d, %I:%M %p")


def format_search_datetime(value):
    if value is None:
        return ""
    if is_russian():
        return (
            f"{value.day} {_MONTHS_RU_ABBREVIATED[value.month - 1]} "
            f"{value.year} {value:%H:%M}"
        )
    try:
        return value.strftime("%b %-d %Y %-I:%M %p")
    except ValueError:
        return value.strftime("%b %d %Y %I:%M %p")


def format_date_button(value):
    if is_russian():
        return f"{value.day} {_MONTHS_RU_ABBREVIATED[value.month - 1]}"
    try:
        return value.strftime("%b %-d")
    except ValueError:
        return value.strftime("%b %d")


def format_time_button(value):
    return value.strftime("%H:%M" if is_russian() else "%I:%M %p").lstrip("0")


def format_created_datetime(value):
    if is_russian():
        return (
            f"{tr('Created')} {value.day} "
            f"{_MONTHS_RU_ABBREVIATED[value.month - 1]} {value.year} · {value:%H:%M}"
        )
    return value.strftime("Created %b %d, %Y · %I:%M %p")


def translate_section(title):
    if not is_russian():
        return title
    if title.startswith("Rest of "):
        month = title.removeprefix("Rest of ")
        if month in _MONTHS_EN:
            return f"Остаток {_MONTHS_RU_GENITIVE[_MONTHS_EN.index(month)]}"
    pieces = title.split()
    if len(pieces) == 3 and pieces[0] in _WEEKDAYS_EN:
        month = pieces[1]
        month_index = next(
            (index for index, name in enumerate(_MONTHS_EN)
             if name.startswith(month)),
            None,
        )
        if month_index is not None:
            weekday = _WEEKDAYS_RU[_WEEKDAYS_EN.index(pieces[0])]
            return f"{weekday}, {pieces[2]} {_MONTHS_RU_ABBREVIATED[month_index]}"
    month, separator, year = title.partition(", ")
    if month in _MONTHS_EN:
        translated = _MONTHS_RU[_MONTHS_EN.index(month)]
        return f"{translated}, {year}" if separator else translated
    return tr(title)