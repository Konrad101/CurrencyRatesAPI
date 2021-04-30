from datetime import timedelta, datetime

import currencies
from api_date_checker_and_parser import parse_datetime_to_str, parse_str_to_date, date_is_correct
from currencies_database import CurrenciesDatabaseManager

SERVER = 'DESKTOP-LKE4F79'
DATABASE_NAME = 'AdventureWorks2019'

MIN_AVAILABLE_YEAR = 2002
API_BASE_CURRENCY = 'PLN'


def get_error_json_with_code_for_data(currency, date, end_date=None):
    currency_available = currency_is_available(currency)
    dates_are_correct = date_is_correct(date)
    if dates_are_correct and end_date is not None:
        dates_are_correct = date_is_correct(end_date)

    if not currency_available:
        if dates_are_correct:
            return create_error_message_json("Wrong currency"), 400
        return create_error_message_json("Wrong request"), 400
    if not dates_are_correct:
        return create_error_message_json("Wrong date"), 400

    date = parse_str_to_date(date)
    if date.year < MIN_AVAILABLE_YEAR or date >= datetime.now().date():
        return create_error_message_json("No data available"), 404
    if end_date is not None:
        end_date = parse_str_to_date(end_date)
        if end_date >= datetime.now().date():
            return create_error_message_json("End date is out of range"), 400
        if date > end_date:
            return create_error_message_json("Start date must be before end date"), 400

    return None


def currency_is_available(currency):
    return currencies.AVAILABLE_CURRENCIES.__contains__(str(currency).upper())


def get_currency_rates(currency, date_from, date_to):
    database_manager = CurrenciesDatabaseManager(SERVER, DATABASE_NAME)
    db_rates = database_manager.get_currency_rates(currency, date_from, date_to)
    if len(db_rates) == 0:
        database_manager.insert_currency_data_to_table(currency, date_from, date_to)
        db_rates = database_manager.get_currency_rates(currency, date_from, date_to)
    else:
        delta = date_to - date_from
        if len(db_rates) < delta.days + 1:
            upload_missing_rows_to_database(database_manager, currency, date_from, date_to)
            db_rates = database_manager.get_currency_rates(currency, date_from, date_to)

    return db_rates


def create_json_from_rates(rates, currency):
    json_respond = {
        "rates": [],
        "currency": str(currency).upper()
    }
    for rate in rates:
        str_date = parse_datetime_to_str(rate[0])
        currency_day_data = {
            "date": str_date,
            "value": rate[1],
            "isInterpolated": rate[2]
        }
        json_respond["rates"].append(currency_day_data)

    return json_respond


def create_error_message_json(message):
    return {"message": message}


def upload_missing_rows_to_database(database, currency, date_from, date_to):
    currency_date = date_from
    last_date = date_from
    empty_data_begin_date = date_from
    empty_data = False
    while currency_date <= date_to:
        date_exist_in_database = database.get_currency_rate_for_date(currency, currency_date) is not None
        if not date_exist_in_database and not empty_data:
            empty_data_begin_date = currency_date
            empty_data = True
        elif date_exist_in_database and empty_data:
            database.insert_currency_data_to_table(currency, empty_data_begin_date, last_date)
            empty_data = False

        last_date = currency_date
        currency_date += timedelta(days=1)

    if empty_data:
        database.insert_currency_data_to_table(currency, empty_data_begin_date, last_date)
