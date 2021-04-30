from datetime import timedelta
from decimal import Decimal

import currencies
from currencies_api import get_currency_rates, API_BASE_CURRENCY
from database_manager import DatabaseManager

SALES_BASE_CURRENCY = 'USD'


class SalesDatabaseManager(DatabaseManager):
    def __create_sales_for_currency_table(self, table_name):
        if table_name is not None:
            self.cursor.execute(f'''
              CREATE TABLE {table_name} (
                    SaleDate DATETIME PRIMARY KEY,
                    TotalSale REAL NOT NULL
              );
            ''')
            self.conn.commit()

    def __get_base_currency_total_sales(self, date_from, date_to):
        self.cursor.execute(
            f"SELECT OrderDate, SUM(TotalDue) FROM Sales.SalesOrderHeader WHERE OrderDate "
            f"BETWEEN '{date_from}' AND '{date_to}' GROUP BY OrderDate ORDER BY OrderDate")
        total_sales_base_currency = []
        for row in self.cursor:
            total_sales_base_currency.append(row)
        return total_sales_base_currency

    def insert_currency_sales_data_to_table(self, currency, date_from, date_to):
        if date_from > date_to:
            raise ValueError("date from must be before date to")

        if str(currency).upper() == API_BASE_CURRENCY.upper():
            self.__update_base_api_currency_table(date_from, date_to)
        else:
            table_name = self.__get_table_name_for_currency(currency)
            if table_name is not None:
                currency_rates = get_currency_rates(currency, date_from, date_to)
                base_api_currency_sales = self.get_total_sales_in_currency(API_BASE_CURRENCY, date_from, date_to)

                currency_sales_data = []
                sale_date = date_from
                index = 0
                while sale_date <= date_to:
                    sale_in_currency = base_api_currency_sales[index][2] / currency_rates[index][1]
                    currency_sales_data.append((sale_date, sale_in_currency))
                    sale_date += timedelta(days=1)
                    index += 1
                self.__insert_sales_data(currency_sales_data, table_name)

    def get_total_sales_in_currency(self, currency, date_from, date_to):
        if str(currency).upper() == SALES_BASE_CURRENCY.upper():
            return self.__get_base_currency_total_sales(date_from, date_to)

        total_sales_base_currency = self.__get_base_currency_total_sales(date_from, date_to)
        sales_in_currency = self.__get_sales_for_currency(currency, date_from, date_to)
        total_sales = []

        index = 0
        for currency_sale in sales_in_currency:
            total_sales.append((total_sales_base_currency[index][0],
                                total_sales_base_currency[index][1],
                                currency_sale[1]))
            index += 1
        return total_sales

    def __update_base_api_currency_table(self, date_from, date_to):
        table_name = self.__get_table_name_for_currency(API_BASE_CURRENCY)
        if table_name is not None:
            base_currency_rates = get_currency_rates(SALES_BASE_CURRENCY, date_from, date_to)
            base_currency_sales = self.__get_base_currency_total_sales(date_from, date_to)
            currency_sales_data = []
            sale_date = date_from
            index = 0
            while sale_date <= date_to:
                sale_in_base_api_currency = Decimal(base_currency_rates[index][1]) * base_currency_sales[index][1]
                currency_sales_data.append((sale_date, sale_in_base_api_currency))
                sale_date += timedelta(days=1)
                index += 1
            self.__insert_sales_data(currency_sales_data, table_name)

    def __get_sales_for_currency(self, currency, date_from, date_to):
        table_name = self.__get_table_name_for_currency(currency)
        if table_name is not None:
            if not self.table_exist_in_database(table_name):
                self.__create_sales_for_currency_table(table_name)
            self.cursor.execute(
                f"SELECT * FROM {table_name} WHERE SaleDate "
                f"BETWEEN '{date_from}' AND '{date_to}' ORDER BY SaleDate")
            sales = []
            for row in self.cursor:
                sales.append(row)
            return sales

    def __insert_sales_data(self, sales_data, table_name):
        if table_name is not None:
            for i in range(len(sales_data)):
                self.cursor.execute(f'''
                    INSERT INTO {table_name} (SaleDate, TotalSale)
                    VALUES (?,?)''',
                                    sales_data[i][0], sales_data[i][1])
            self.conn.commit()
            return True
        return False

    @staticmethod
    def __get_table_name_for_currency(currency):
        if currencies.AVAILABLE_CURRENCIES.__contains__(str(currency).upper()) or \
                str(currency).upper() == API_BASE_CURRENCY:
            return str(currency).upper() + '_Sales'
        else:
            return None

    def get_currency_sale_for_date(self, currency, date):
        table_name = self.__get_table_name_for_currency(currency)
        if table_name is not None:
            if not self.table_exist_in_database(table_name):
                self.__create_sales_for_currency_table(table_name)
            self.cursor.execute(
                f"SELECT SaleDate, TotalSale FROM {table_name} "
                f"WHERE SaleDate = '{date}' "
            )
            return self.cursor.fetchone()
        return None
