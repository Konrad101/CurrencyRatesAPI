import json
from datetime import date, timedelta

import dateutil.parser
import requests

NO_DATA_RESPONSE = '404 NotFound - Not Found - Brak danych'


def get_url_data(url):
    try:
        request = requests.get(url)
        json_data = json.loads(request.text)
        return json_data
    except requests.exceptions.ConnectionError:
        print('No connection')
    except json.decoder.JSONDecodeError as err:
        if err.doc != NO_DATA_RESPONSE:
            print('Error occurred while decoding JSON: ', err.doc)
    return None


class CurrencyDataDownloader:
    def __init__(self, currency):
        self.__base_link = 'http://api.nbp.pl/api/'
        self.__currency_table_type = 'A'
        self.__MAX_DAYS_AMOUNT = 367
        self.__currency = currency

    def __get_currency_rate_json(self, rate_date):
        link_to_data = self.__base_link + f'exchangerates/rates/{self.__currency_table_type}/' \
                                          f'{str(self.__currency).lower()}/{str(rate_date)}/'
        json_data = get_url_data(link_to_data)
        currency_code = ''
        if json_data is not None:
            if isinstance(json_data, list):
                currency_code = json_data[0]['code']
            elif isinstance(json_data, dict):
                currency_code = json_data['code']
                json_data = [json_data]
        return json_data, currency_code

    def __get_currency_rates_json_data(self, date_from, date_to):
        json_multiple_data = []
        last_date = False
        part_date_to = date_from + timedelta(days=self.__MAX_DAYS_AMOUNT)
        if part_date_to > date_to:
            part_date_to = date_to

        while part_date_to <= date_to:
            link_to_data = self.__base_link + f'exchangerates/rates/{self.__currency_table_type}/' \
                                              f'{str(self.__currency).lower()}/{str(date_from)}/{str(part_date_to)}/'
            json_multiple_data.append(get_url_data(link_to_data))
            date_from = part_date_to + timedelta(days=1)
            part_date_to = date_from + timedelta(days=self.__MAX_DAYS_AMOUNT)
            if part_date_to > date_to > date_from and not last_date:
                part_date_to = date_to
                last_date = True
        currency_code = ''
        if len(json_multiple_data) > 0 and json_multiple_data[0] is not None:
            currency_code = json_multiple_data[0]['code']

        return json_multiple_data, currency_code

    def get_currency_prices_for_dates(self, date_from, date_to):
        json_data = self.__get_currency_rates_json_data(date_from, date_to)
        return self.__get_result_from_json_data(json_data)

    def get_currency_prices_for_date(self, rate_date):
        json_data = self.__get_currency_rate_json(rate_date)
        return self.__get_result_from_json_data(json_data)

    def get_currency_prices_for_last_days(self, how_many_days):
        date_from = date.today() - timedelta(days=how_many_days)
        date_to = date.today()
        if date_to > date.today():
            date_to = date.today()
        json_data = self.__get_currency_rates_json_data(date_from, date_to)
        return self.__get_result_from_json_data(json_data)

    def get_currency_prices_for_last_half_year(self):
        date_six_months_ago = date.today() - dateutil.relativedelta.relativedelta(months=6)
        delta = date.today() - date_six_months_ago
        return self.get_currency_prices_for_last_days(delta.days)

    @staticmethod
    def __get_result_from_json_data(json_data):
        prices_with_dates = []
        if json_data[0] is not None and json_data[0][0] is not None:
            for data in json_data[0]:
                for rate in data['rates']:
                    prices_with_dates.append((rate['effectiveDate'], rate['mid']))
        return prices_with_dates, json_data[1]
