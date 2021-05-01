from datetime import timedelta, datetime

import currencies
from api_date_checker_and_parser import parse_str_to_date, parse_datetime_to_str, date_is_correct
from currencies_api import API_BASE_CURRENCY
from sales_database import SalesDatabaseManager, SALES_BASE_CURRENCY


MIN_AVAILABLE_DATE = datetime(2011, 5, 31)
MAX_AVAILABLE_DATE = datetime(2014, 6, 30)


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
    if date < MIN_AVAILABLE_DATE.date() or date > MAX_AVAILABLE_DATE.date():
        return create_error_message_json("No data available"), 404
    if end_date is not None:
        end_date = parse_str_to_date(end_date)
        if end_date > MAX_AVAILABLE_DATE.date():
            return create_error_message_json("End date is out of range"), 400
        if date > end_date:
            return create_error_message_json("Start date must be before end date"), 400

    return None


def create_error_message_json(message):
    return {"message": message}


def currency_is_available(currency):
    return currencies.AVAILABLE_CURRENCIES.__contains__(str(currency).upper()) or \
           str(currency).upper() == API_BASE_CURRENCY.upper()


def create_json_from_sales(sales, currency):
    json_respond = {
        "sales": [],
        "originalCurrency": SALES_BASE_CURRENCY.upper(),
        "chosenCurrency": str(currency).upper()
    }
    for sale in sales:
        str_date = parse_datetime_to_str(sale[0])
        if str(currency).upper() == SALES_BASE_CURRENCY.upper():
            currency_day_data = {
                "date": str_date,
                "saleOriginalCurrency": float(sale[1]),
            }
        else:
            currency_day_data = {
                "date": str_date,
                "saleOriginalCurrency": float(sale[1]),
                "saleCurrency": float(sale[2])
            }
        json_respond["sales"].append(currency_day_data)

    return json_respond


def get_sales_for_date_and_currency(currency, date_from, date_to):
    database_manager = SalesDatabaseManager()
    update_currency_sales(database_manager, API_BASE_CURRENCY, date_from, date_to)
    if currency != API_BASE_CURRENCY:
        update_currency_sales(database_manager, currency, date_from, date_to)

    currency_sales = database_manager.get_total_sales_in_currency(currency, date_from, date_to)
    return currency_sales


def update_currency_sales(db_manager, currency, date_from, date_to):
    currency_sales = db_manager.get_total_sales_in_currency(currency, date_from, date_to)
    if len(currency_sales) == 0:
        db_manager.insert_currency_sales_data_to_table(currency, date_from, date_to)
    else:
        delta = date_to - date_from
        if len(currency_sales) < delta.days + 1:
            upload_missing_rows_to_database(db_manager, currency, date_from, date_to)


def upload_missing_rows_to_database(db_manager, currency, date_from, date_to):
    sale_date = date_from
    last_date = date_from
    empty_data_begin_date = date_from
    empty_data = False
    while sale_date <= date_to:
        date_exist_in_database = db_manager.get_currency_sale_for_date(currency, sale_date) is not None
        if not date_exist_in_database and not empty_data:
            empty_data_begin_date = sale_date
            empty_data = True
        elif date_exist_in_database and empty_data:
            db_manager.insert_currency_sales_data_to_table(currency, empty_data_begin_date, last_date)
            empty_data = False

        last_date = sale_date
        sale_date += timedelta(days=1)

    if empty_data:
        db_manager.insert_currency_sales_data_to_table(currency, empty_data_begin_date, last_date)
