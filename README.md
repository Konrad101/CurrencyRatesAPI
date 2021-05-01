# CurrencyRatesAPI


# Project requirements

Flask==1.1.2

pyodbc==4.0.30

Flask_RESTful==0.3.8

Flask_Limiter==1.4

requests==2.25.1

python_dateutil==2.8.1

To run the server, an SQL database 'AdventureWorks2019' is required. 

# Hints

By default the server starts on port 5000. 

If you want to run the server on different port number, you need to run the server - [`main.py`](main.py) script with optional parameter:

```text
main.py [-p PORT]

arguments:
-p PORT or --port PORT    is responsible for setting the port on which the server will be running
```

Sales database contains data from 2011-05-31 to 2014-06-30.

# Requests

### server_addres, for example: http://127.0.0.1:5000/

### currency, for example: USD

### date of format YYYY-MM-DD, for example: 2013-07-23

## Sample requests for currency rates: 

server_address/currency-rates/\<currency>/\<start_date>/\<end_date>

server_address/currency-rates/\<currency>/\<date>

## Sample requests for sales: 

server_address/sales/\<currency>/\<start_date>/\<end_date>

server_address/sales/\<currency>/\<date>

# Server response

## Examples

### Currency rates:

#### /currency-rates/USD/2021-04-29

```json
{
    "rates": [
        {
            "date": "2021-04-29",
            "value": 3.778599977493286,
            "isInterpolated": false
        }
    ],
    "currency": "USD"
}
```

#### /currency-rates/USD/2021-04-27/2021-04-29

```json
{
    "rates": [
        {
            "date": "2021-04-27",
            "value": 3.782599925994873,
            "isInterpolated": false
        },
        {
            "date": "2021-04-28",
            "value": 3.7939000129699707,
            "isInterpolated": false
        },
        {
            "date": "2021-04-29",
            "value": 3.778599977493286,
            "isInterpolated": false
        }
    ],
    "currency": "USD"
}
```

#### /currency-rates/USD/2021.04.29

```json
{
    "message": "Wrong date"
}
```

### Sales:

#### /sales/EUR/2013-01-01

```json
{
    "sales": [
        {
            "date": "2013-01-01",
            "saleOriginalCurrency": 21684.4068,
            "saleCurrency": 16440.73046875
        }
    ],
    "originalCurrency": "USD",
    "chosenCurrency": "EUR"
}
```

#### /sales/EUR/2013-01-01/2013-01-03

```json
{
    "sales": [
        {
            "date": "2013-01-01",
            "saleOriginalCurrency": 21684.4068,
            "saleCurrency": 16440.73046875
        },
        {
            "date": "2013-01-02",
            "saleOriginalCurrency": 12489.2087,
            "saleCurrency": 9415.041015625
        },
        {
            "date": "2013-01-03",
            "saleOriginalCurrency": 34090.4269,
            "saleCurrency": 25925.28125
        }
    ],
    "originalCurrency": "USD",
    "chosenCurrency": "EUR"
}
```

#### /sales/USD/2013-01-01/2020-01-03

```json
{
    "message": "End date is out of range"
}
```

#### /sales/USD/2013-01-03/2013-01-01

```json
{
    "message": "Start date must be before end date"
}
```
