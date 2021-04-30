# CurrencyRatesAPI


# Project requirements

Flask==1.1.2

pyodbc==4.0.30

Flask_RESTful==0.3.8

Flask_Limiter==1.4

requests==2.25.1

python_dateutil==2.8.1

# Hints

Usually the server starts on port 5000

# Requests

### server_addres, for example: http://127.0.0.1:5000/

### currency, for example: USD

### date, for example: 2013-07-23

## Requests for currency rates: 

server_address/currency-rates/currency/start_date/end_date

server_address/currency-rates/currency/date

## Requests for sales: 

server_address/sales/currency/start_date/end_date

server_address/sales/currency/date