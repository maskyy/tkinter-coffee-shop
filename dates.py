import datetime as _dt

_date_format = "%Y-%m-%d"


def to_date(s):
    try:
        return _dt.datetime.strptime(s, _date_format).date()
    except ValueError:
        return False


def from_date(date):
    return date.strftime(_date_format)
