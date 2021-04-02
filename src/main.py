import re

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from driver import chrome_driver


# Constants
DRIVER_PATH = './chromedriver'
CORPORATIONS_FILE_PATH = './Data/corporation.csv'
MARKET_PRICES_FILE_PATH = './Data/market_price.csv'

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
    for row_num, row in enumerate(table.find_elements_by_tag_name('tr')):
        # Remove headers.
        if row_num != 0:
            row_lst = list(append_fields)
            for col_num, cell in enumerate(row.find_elements_by_tag_name('td')):
                # Get links.
                if col_num in link_at_cols:
                    link = cell.find_element_by_tag_name('a')
                    row_lst.append(link.get_attribute('href'))
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

def write_list_to_file(lst, file_path):
    with open(file_path, 'w') as f:
        for row in lst:
            for itm in row:
                f.write(f'"{itm}",')
            f.write('\n')


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
            append_fields= (corporation[ISIN_COL],)
        )

    # Output the tables to csv files.
    write_list_to_file(corporations_list, CORPORATIONS_FILE_PATH)
    write_list_to_file(market_prices_list, MARKET_PRICES_FILE_PATH)

    #Quit the driver.
    driver.quit()
