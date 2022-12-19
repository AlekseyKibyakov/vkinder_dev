import datetime as dt


def string_with_born_to_age(born: str) -> int:
    today = dt.date.today()
    born = dt.datetime.strptime(born, "%d.%m.%Y")
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))