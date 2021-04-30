from datetime import datetime


def parse_str_to_date(str_datetime):
    return datetime.strptime(str_datetime, '%Y-%m-%d').date()


def parse_datetime_to_str(date):
    return date.strftime('%Y-%m-%d')


def date_is_correct(date):
    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        return False
    return True
