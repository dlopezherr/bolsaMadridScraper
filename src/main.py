import re

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import csv

from driver import chrome_driver


# Constants
DRIVER_PATH = '../res/chromedriver'
CORPORATIONS_FILE_PATH = '../data_scraped/corporation.csv'
MARKET_PRICES_FILE_PATH = '../data_scraped/market_price.csv'

MAIN_TABLE_URL = 'https://www.bolsamadrid.es/esp/aspx/Empresas/Empresas.aspx'
MAIN_TABLE_ID = 'ctl00_Contenido_tblEmisoras'
MAIN_TABLE_NEXT_BTN_ID = 'ctl00_Contenido_SiguientesArr'


GENERAL_INFO_RESOURCE_NAME = 'FichaValor'
MARKET_PRICE_RESOURCE_NAME = 'InfHistorica'
MARKET_PRICE_TABLE_ID = 'ctl00_Contenido_tblDatos'
MARKET_PRICE_NEXT_BTN_ID = 'ctl00_Contenido_SiguientesArr'
ISIN_COL = 0
ISIN_REGEX = r'ISIN=(.+)'

NEXT_BUTTON_DELAY = 2
TABLE_DELAY = 10


def parse_table_page(table, results_list, link_at_cols=(), append_fields=()):
    """Parse a selenium item containing an html table.

    This function parses an html table to a list of lists. It extracts the
    textual contents of the table as well as the links on the columns indicated
    in links_at_cols argument. Headers row (first row) is skipped.
    :param table: (selenium object): Selenium object containing an html table.
    :param results_list: (list): List where the results are appended.
    :param link_at_cols: (iterable): Optional iterable contain the column numbers
    where there are hyperlinks to be parsed.
    :param append_fields: (iterable): Optional iterable containing any items which
    need be prepended to each row.
    :return: The list results_list received as an argument.
    """
    for row_num, row in enumerate(table.find_elements_by_tag_name('tr')):
        # Remove headers.
        if row_num != 0:
            row_lst = list(append_fields)
            for col_num, cell in enumerate(row.find_elements_by_tag_name('td')):
                # Get links.
                try:
                    if col_num in link_at_cols:
                        link = cell.find_element_by_tag_name('a')
                        row_lst.append(link.get_attribute('href'))
                except NoSuchElementException as e:
                    err_msg = (f'An error has occurred parsing the link from row {row_num}'
                               f' and column {col_num} at table {table.get_attribute("id")}:\n'
                               f'  Error message: {e.msg}\n'
                               f'  Source code: {cell.get_attribute("innerHTML")}\n')
                    raise Exception(err_msg)
                # Get text.
                row_lst.append(cell.text)
            results_list.append(row_lst)
    return results_list


def parse_main_page(driver, results_list, table_id, next_btn_id, link_at_cols=(), append_fields=()):
    
    try:
        while True:
            table = WebDriverWait(driver, TABLE_DELAY).until(
                EC.presence_of_element_located((By.ID, table_id))
            )
            results_list = parse_table_page(table, results_list, link_at_cols, append_fields)
            next_page_btn = WebDriverWait(driver, NEXT_BUTTON_DELAY).until(
                EC.presence_of_element_located((By.ID, next_btn_id))
            )
            next_page_btn.click()
    except Exception as e:
        print(type(e))
    return results_list

def write_list_to_file(lst, file_path, mode='w'):
    """Write a table contained in a list of list to a file.

    :param lst: (list) List containing the rows of the table.
    :param file_path: (str) String containing the file path.
    :param mode: (str) File open mode.
    """
    with open(file_path, mode) as f:
        writer = csv.writer(f)
        writer.writerows(lst)


if __name__ == '__main__':
    corporations_list = []
    market_prices_list = []

    # Get corporations table as a list of lists.
    driver = chrome_driver(DRIVER_PATH)
    driver.get(MAIN_TABLE_URL)   # HTTP request.
    corporations_list = parse_main_page(
        driver,
        results_list=corporations_list,
        table_id=MAIN_TABLE_ID,
        next_btn_id=MAIN_TABLE_NEXT_BTN_ID,
        link_at_cols=(ISIN_COL, )
    )

    print(len(corporations_list))

    # Get market_prices table as a list of lists.
    for corporation in corporations_list:
        # Adapt URL.
        url = corporation[ISIN_COL].replace(GENERAL_INFO_RESOURCE_NAME, MARKET_PRICE_RESOURCE_NAME)
        # Parse ISIN.
        corporation[ISIN_COL] = re.findall(ISIN_REGEX, corporation[ISIN_COL])[0]
        driver.get(url)
        market_prices_list = parse_main_page(
            driver,
            results_list=market_prices_list,
            table_id=MARKET_PRICE_TABLE_ID,
            next_btn_id=MAIN_TABLE_NEXT_BTN_ID,
            link_at_cols=tuple(),
            append_fields=(corporation[ISIN_COL],)
        )


    # Output the tables to csv files.
    write_list_to_file(corporations_list, CORPORATIONS_FILE_PATH, 'w')
    write_list_to_file(market_prices_list, MARKET_PRICES_FILE_PATH, 'w')

    # Quit the driver.
    driver.quit()
