import sys
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
from queue import Queue
import csv

from webparser import WebParserThread, Task

# Constants
# Chrome driver and result files path.
DRIVER_PATH = '../res/chromedriver'
CORPORATIONS_FILE_PATH = '../data_scraped/corporation.csv'
MARKET_PRICES_FILE_PATH = '../data_scraped/market_price.csv'

# Main table ids.
MAIN_TABLE_URL = 'https://www.bolsamadrid.es/esp/aspx/Empresas/Empresas.aspx'
MAIN_TABLE_ID = 'ctl00_Contenido_tblEmisoras'
MAIN_TABLE_NEXT_BTN_ID = 'ctl00_Contenido_SiguientesArr'

# ISIN extraction info.
ISIN_COL = 0
ISIN_REGEX = r'ISIN=(.+)'

# Ids of the historic data time window formulary required fields.
FORM_START_DAY_ID = 'ctl00_Contenido_Desde_Dia'
FORM_START_MONTH_ID = 'ctl00_Contenido_Desde_Mes'
FORM_START_YEAR_ID = 'ctl00_Contenido_Desde_Año'
FORM_SEND_BTN_ID = 'ctl00_Contenido_Buscar'
TIME_DELTA_MONTHS = 12      # Number of months extracted.

# Market price table ids.
MARKET_PRICE_BASE_URL = 'https://www.bolsamadrid.es/esp/aspx/Empresas/InfHistorica.aspx?ISIN='
MARKET_PRICE_TABLE_ID = 'ctl00_Contenido_tblDatos'
MARKET_PRICE_NEXT_BTN_ID = 'ctl00_Contenido_SiguientesArr'

# Number of workers in the pool, base timeout and number of trials.
NUM_OF_THREADS = 8
BASE_TIMEOUT = 30   # Delay to let the server recover is (30*2^k)
NUM_OF_TRIALS = 3   # with k increasing from 0 to NUM_OF_TRIALS - 1.


def write_list_to_file(lst, file_path, mode='w'):
    """Write a table contained in a list of list to a file.

    :param lst: (list) List containing the rows of the table.
    :param file_path: (str) String containing the file path.
    :param mode: (str) File open mode.
    """
    with open(file_path, mode) as f:
        writer = csv.writer(f)
        writer.writerows(lst)


def is_succesfull(itm, failed_list):
    """Append error message to the error list when an exception is received.

    :param itm: item checked.
    :param failed_list: List of errors.
    :return: When an exception is received, return None. Elsewise, return itm.
    """
    if isinstance(itm, Exception):
        failed_list.append(str(itm))
        return None
    else:
        return itm


if __name__ == '__main__':

    errors = []

    # Create queues.
    in_q = Queue()
    out_q = Queue()

    # Get the main table.
    t = WebParserThread(DRIVER_PATH, in_q, out_q, base_timeout=BASE_TIMEOUT,
                        retry_times=NUM_OF_TRIALS)
    t.set_table(MAIN_TABLE_ID, MAIN_TABLE_NEXT_BTN_ID, (ISIN_COL,))
    t.start()
    in_q.put(Task(MAIN_TABLE_URL))
    in_q.put(None)
    in_q.join()
    main_table = is_succesfull(out_q.get(), errors)
    if main_table is None:
        print('The process failed to extract Main Table. '
              'Please check the errors or try again later.\n  Errors:')
        for error in errors:
            print(error)
        sys.exit()
    print(f'Main Table has of {len(main_table)} registers.')

    # Configure a parser for market price trable data extraction.
    query_start_date = datetime.today() - relativedelta(months=12)
    form_fields = {}
    form_fields[FORM_START_DAY_ID] = query_start_date.day
    form_fields[FORM_START_MONTH_ID] = query_start_date.month
    form_fields[FORM_START_YEAR_ID] = query_start_date.year

    # Create a pool of daemon workers.
    threads = []
    for i in range(NUM_OF_THREADS):
        t = WebParserThread(DRIVER_PATH, in_q, out_q, base_timeout=BASE_TIMEOUT,
                            retry_times=NUM_OF_TRIALS)
        t.set_table(MARKET_PRICE_TABLE_ID, MARKET_PRICE_NEXT_BTN_ID)
        t.set_form(form_fields, FORM_SEND_BTN_ID)
        t.start()
        threads.append(t)

    # Load urls and ISINs into the queue.
    for row in main_table:
        row[ISIN_COL] = re.findall(ISIN_REGEX, row[ISIN_COL])[0]
        url = f'{MARKET_PRICE_BASE_URL}{row[ISIN_COL]}'
        in_q.put(Task(url, (row[ISIN_COL],)))
    # Write main table to file.

    write_list_to_file(main_table, CORPORATIONS_FILE_PATH)

    # Add terminal threads terminal signal to the queue.
    for _ in range(NUM_OF_THREADS):
        in_q.put(None)

    # Truncate file.
    with open(MARKET_PRICES_FILE_PATH, 'w') as f:
        f.truncate()

    # Process results
    for count in range(len(main_table)):
        corp_data = is_succesfull(out_q.get(), errors)
        if corp_data is not None:
            print(f'Corporation with ISIN = {corp_data[0][0]} correctly downloaded.'
                  f' Download: {count/len(main_table)*100:.2f}% completed.')
            write_list_to_file(corp_data, MARKET_PRICES_FILE_PATH, 'a')

    # Report Error.
    print("\n\nErrors:")
    for error in errors:
        print(error)
