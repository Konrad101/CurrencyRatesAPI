from abc import ABC

import pyodbc


class DatabaseManager(ABC):
    def __init__(self, server, database):
        self.min_available_year = 2002
        self.conn = pyodbc.connect(
            "Driver={SQL Server Native Client 11.0};"
            f"Server={server};"
            f"Database={database};"
            "Trusted_Connection=yes;"
        )
        self.server = server
        self.database_name = database
        self.cursor = self.conn.cursor()

    def table_exist_in_database(self, table_name):
        if table_name is not None:
            return self.cursor.tables(table=table_name, tableType='TABLE').fetchone()
        return False
