from datetime import datetime
from datetime import timedelta
from currency_api_connector import CurrencyDataDownloader
from database_manager import DatabaseManager
import currencies


class CurrenciesDatabaseManager(DatabaseManager):
    def __create_currency_table(self, table_name):
        if table_name is not None:
            self.cursor.execute(f'''
              CREATE TABLE {table_name} (
                    QuotationDate DATETIME PRIMARY KEY,
                    CurrencyRate REAL NOT NULL,
                    Interpolated BIT NOT NULL
              );
            ''')
            self.conn.commit()

    def insert_currency_data_to_table(self, currency, date_from, date_to):
        if date_from > date_to:
            raise ValueError("date from must be before date to")

        table_name = self.__get_table_name_for_currency(currency)
        if table_name is not None:
            if not self.table_exist_in_database(table_name):
                self.__create_currency_table(table_name)
            currency_data_downloader = CurrencyDataDownloader(currency)
            currency_data = currency_data_downloader.get_currency_prices_for_dates(date_from, date_to)
            return self.__create_rates_and_insert_data(currency_data, date_from, date_to, currency, table_name)
        return None

    def __create_rates_and_insert_data(self, currency_data, date_from, date_to, currency, table_name):
        dates = []
        interpolation_statements = []
        api_data_is_not_empty = currency_data[0] is not None and len(currency_data[0]) > 0
        if api_data_is_not_empty:
            rate_date = date_from
            while rate_date <= date_to:
                dates.append(rate_date)
                rate_date += timedelta(days=1)
            currency_rates_data = self.__create_currency_rates_for_dates(currency_data, date_from, date_to)
            currency_rates = currency_rates_data[0]
            interpolation_statements = currency_rates_data[1]
        else:
            last_available_rate = self.__get_first_available_rate_from_date(date_from, currency)
            rate_date = date_from
            currency_rates = []
            while rate_date <= date_to:
                currency_rates.append(last_available_rate)
                interpolation_statements.append(True)
                dates.append(rate_date)
                rate_date += timedelta(days=1)

        return self.__insert_currency_data(dates, currency_rates, interpolation_statements, table_name)

    def __create_currency_rates_for_dates(self, currency_data, date_from, date_to):
        rates_with_interpolation = self.__get_rates_and_interpolation_from_currency_data(currency_data, date_from)
        currency_rates = rates_with_interpolation[0]
        interpolation_statements = rates_with_interpolation[1]
        last_rate = currency_rates[-1]
        last_date = datetime.strptime(currency_data[0][-1][0], '%Y-%m-%d')
        if last_date != date_to:
            missing_data = self.__create_interpolated_data(last_date,
                                                           datetime.combine(date_to, datetime.min.time()),
                                                           last_rate)
            currency_rates += missing_data[0]
            interpolation_statements += missing_data[1]

        return currency_rates, interpolation_statements

    def __get_rates_and_interpolation_from_currency_data(self, currency_data, date_from):
        currency_rates = []
        interpolation_statements = []
        last_date = datetime.strptime(currency_data[0][0][0], '%Y-%m-%d')
        last_rate = self.__get_first_available_rate_from_date(last_date, currency_data[1])
        first_iteration = True
        for data in currency_data[0]:
            rate_date = datetime.strptime(data[0], '%Y-%m-%d')
            if first_iteration and rate_date != date_from:
                missing_data = self.__create_interpolated_data(datetime.combine(date_from, datetime.min.time()),
                                                               rate_date - timedelta(days=1),
                                                               last_rate)
                currency_rates += missing_data[0]
                interpolation_statements += missing_data[1]
                first_iteration = False

            delta = rate_date - last_date
            if delta.days > 1:
                for days_diff in range(delta.days - 1):
                    currency_rates.append(last_rate)
                    interpolation_statements.append(True)
                currency_rates.append(data[1])
                interpolation_statements.append(False)
            else:
                currency_rates.append(data[1])
                interpolation_statements.append(False)
            last_rate = data[1]
            last_date = rate_date
        return currency_rates, interpolation_statements

    @staticmethod
    def __create_interpolated_data(date_from, date_to, rate):
        rate_date = date_from
        currency_rates = []
        interpolation_statements = []
        while rate_date <= date_to:
            currency_rates.append(rate)
            interpolation_statements.append(True)
            rate_date += timedelta(days=1)
        return currency_rates, interpolation_statements

    def __get_first_available_rate_from_date(self, rate_date, currency):
        currency_data_downloader = CurrencyDataDownloader(currency)
        last_available_rate = 0
        last_available_rate_date = rate_date - timedelta(days=1)
        while last_available_rate == 0 and last_available_rate_date.year >= self.min_available_year:
            str_date = datetime.strftime(last_available_rate_date, '%Y-%m-%d')
            rate_data = self.get_currency_rate_for_date(currency, str_date)
            if rate_data is None:
                rate_data = currency_data_downloader. \
                    get_currency_prices_for_date(str_date)
                if len(rate_data[0]) > 0 and rate_data[0][0] is not None:
                    last_available_rate = rate_data[0][0][1]
            else:
                last_available_rate = rate_data[1]
            last_available_rate_date -= timedelta(days=1)

        return last_available_rate

    def __insert_currency_data(self, dates, currency_rates, interpolation_statements, table_name):
        if table_name is not None:
            for i in range(len(dates)):
                self.cursor.execute(f'''
                    INSERT INTO {table_name} (QuotationDate, CurrencyRate, Interpolated)
                    VALUES (?,?,?)''',
                                    dates[i], currency_rates[i], interpolation_statements[i])
            self.conn.commit()
            return True
        return False

    @staticmethod
    def __get_table_name_for_currency(currency):
        if currencies.AVAILABLE_CURRENCIES.__contains__(str(currency).upper()):
            return str(currency).upper() + '_Currency'
        else:
            return None

    def get_currency_rates(self, currency, date_from, date_to):
        table_name = self.__get_table_name_for_currency(currency)
        if table_name is not None:
            if not self.table_exist_in_database(table_name):
                self.__create_currency_table(table_name)
            self.cursor.execute(
                f"SELECT * FROM {table_name} WHERE QuotationDate "
                f"BETWEEN '{date_from}' AND '{date_to}' ORDER BY QuotationDate")
            rates = []
            for row in self.cursor:
                rates.append(row)
            return rates
        return None

    def get_currency_rate_for_date(self, currency, date):
        table_name = self.__get_table_name_for_currency(currency)
        if table_name is not None:
            if not self.table_exist_in_database(table_name):
                self.__create_currency_table(table_name)
            self.cursor.execute(
                f"SELECT QuotationDate, CurrencyRate FROM {table_name} "
                f"WHERE QuotationDate = '{date}' "
            )
            return self.cursor.fetchone()
        return None
