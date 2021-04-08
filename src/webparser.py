"""This module is used to extract a java script loaded table from a website."""

import threading
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium import webdriver


def chrome_driver(driver_path):
    """Configure a Chrome webdriver."""
    options = webdriver.ChromeOptions()
    options.headless = True
    options.add_argument('--start-maximized')
    options.add_argument('--disable-extensions')
    driver = webdriver.Chrome(executable_path=driver_path, chrome_options=options)
    return driver


class Task:
    """Contains an URL and a set of fields"""
    def __init__(self, url, append_fields=()):
        self.url = url
        self.append_fields = append_fields


class WebParserThread(threading.Thread):
    """Thread class to parse an html table loaded with java-script from a web page.

    This classes parses a java-script loaded multipage html table to a list of list
    from the web page URL. It supports the automatic submission of a formulary prior
    to table extraction, extraction of hyperlinks from a set of table columns and the
    addition of a set of values to all rows in a table.
    Web navigation takes place in a daemon thread. The results are posted onto the
    output queue. When an error is captured,it is posted on the output queue and the
    thread is terminated.

    Usage:
        1. Create an object.
        2. Define the table to parse using 'set_table()'.
        3. (Optional) Configure the submission of a form prior to table data extraction
        process, using 'set_form()' method.
        4. Start the thread with 'start()' method.
        5. Feed Task objects to the input queue with the pages to be parsed. The task
        will contain the website URL and the values to be appended to each row of the
        table (by default, an empty tuple).
        7. Feed a null reference (None) to the input queue to terminate the thread loop.

    Simple example:
        form_ids = {'year_field':'1989'}
        t = WebParserThread(driver_path, in_q, out_q)
        t.set_table(table_id, next_btn_id)
        t.set_form(form_ids, summit_form_btn_id)
        t.start()
        in_q.put(Task(URL))
        in_q.put(None)
        out.q.get()
    """

    def __init__(self, driver_path, in_q, out_q, timeout=30):
        """Initialize object fields."""
        threading.Thread.__init__(self, daemon=True)
        self.driver_path = driver_path
        self.driver = None
        self.in_q = in_q
        self.out_q = out_q
        self.timeout = timeout
        self.id_table = ""
        self.id_table_next_btn = ""
        self.link_at_cols = ()
        self.append_fields = ()
        self.has_form = False
        self.ids_form_dict = None
        self.id_form_next_btn = ""
        self.results = []

    def __start_driver(self):
        """Start selenium webdriver object."""
        if self.driver is None:
            self.driver = chrome_driver(self.driver_path)

    def __close_driver(self):
        """Quit webdriver."""
        if self.driver is not None:
            self.driver.quit()

    def __set_hyperlinks_extraction(self, links_at_cols):
        """Configures the extraction of links form a set of columns of the table."""
        assert hasattr(links_at_cols, '__iter__'), \
            'Error! links_at_cols argument must be an iterable'
        self.link_at_cols = links_at_cols

    def __set_appended_fields_to_table(self, append_fields):
        """Configure a set of values to be appended to each row of the result table.

        :param append_fields: (iterable) Set of values to be appended to each row
        of the table.
        """
        assert hasattr(append_fields, '__iter__'), \
            'Error! append_fields argument must be an iterable'
        self.append_fields = append_fields

    def __parse_table_page(self, table):
        """Parse a selenium element containing an html table and appends it to self.results.

        This function parses an html table and appends it to a list of lists. It extracts
        the textual contents of the table as well as the links on the columns configured
        with __set_hyperlinks_extraction(). The addition to all rows of a set of constant
        values can be set up with __set_appended_fields_to_table(). Headers row
        (first row) is skipped. The results are appended to self.results list.
        :param table: (selenium object): Selenium object containing an html table.
        """
        for row_num, row in enumerate(table.find_elements_by_tag_name('tr')):
            # Skip headers.
            if row_num != 0:
                row_lst = list(self.append_fields)
                for col_num, cell in enumerate(row.find_elements_by_tag_name('td')):
                    # Extract hyperlink.
                    try:
                        if col_num in self.link_at_cols:
                            link = cell.find_element_by_tag_name('a')
                            row_lst.append(link.get_attribute('href'))
                    except NoSuchElementException as e:
                        err_msg = (f'An error has occurred parsing the link from row {row_num}'
                                   f' and column {col_num} at table {table.get_attribute("id")}:\n'
                                   f'  Error message: {e.msg}\n'
                                   f'  Source code: {cell.get_attribute("innerHTML")}\n')
                        raise Exception(err_msg)
                    # Extract text.
                    row_lst.append(cell.text)
                # Append results
                self.results.append(row_lst)

    def __fill_formulary(self):
        """Fill and submit a web formulary from a dictionary.

        This function fills a web formulary from the contents of a dictionary
        which contains the textboxes ids as keys and the the values to be input
        as its associated values.
        """
        for elem_id, val in self.ids_form_dict.items():
            try:
                elem = WebDriverWait(self.driver, self.timeout).until(
                    ec.presence_of_element_located((By.ID, elem_id))
                )
                elem.send_keys(Keys.CONTROL, "a")
                elem.send_keys(str(val))
            except TimeoutException as e:
                err_msg = (f'Program timed out waiting for element with id = {elem_id}:\n'
                           f'  Error message: {e.msg}\n')
                raise Exception(err_msg)
        try:
            send_btn = WebDriverWait(self.driver, self.timeout).until(
                ec.presence_of_element_located((By.ID, self.id_form_next_btn))
            )
            send_btn.click()
        except TimeoutException as e:
            err_msg = (f'Program timed out waiting for formulary button, with id = '
                       f'{self.id_form_next_btn}:\n  Error message: {e.msg}\n')
            raise Exception(err_msg)

    def __parse_page(self, url):
        """Extract the contents of an HTML table to a list of lists.

        The extraction results are appended to self.results list.
        :param url: (str) URL of the website where the table to be extracted is
        located.
        """
        if self.driver is None:
            self.__start_driver()
        self.driver.get(url)
        if self.has_form:
            self.__fill_formulary()
        try:
            while True:
                table = WebDriverWait(self.driver, self.timeout).until(
                    ec.presence_of_element_located((By.ID, self.id_table))
                )
                self.__parse_table_page(table)
                next_page_btn = self.driver.find_element_by_id(self.id_table_next_btn)
                next_page_btn.click()
        except NoSuchElementException:
            pass
        except Exception as e:
            self.out_q.put(e)

    def run(self):
        """Process jobs from an input queue.

        Get jobs from in_q, process it and return the results to out_q. All excepted
        exceptions are posted to out_queue. The functions loops until None is got from
        the input queue.
        """
        while True:
            task = self.in_q.get()
            if task is None:
                self.in_q.task_done()
                self.__close_driver()
                return
            self.__set_appended_fields_to_table(task.append_fields)
            self.__parse_page(task.url)
            self.out_q.put(self.results)
            self.results = []
            self.in_q.task_done()

    def set_table(self, id_table, id_next_btn, links_at_cols=()):
        """Configures the ids of the table to be parsed.

        :param id_table: (str) HTML id of the table.
        :param id_next_btn: (str) HTML id of the table's next page button.
        :param links_at_cols: (iterable) Iterable with the numbers of columns
        from which hyperlinks are to be extracted.
        """
        self.id_table = id_table
        self.id_table_next_btn = id_next_btn
        self.__set_hyperlinks_extraction(links_at_cols)

    def set_form(self, fields_id_dict, id_next_btn):
        """Configure the submission of a formulary prior to table parsing.

        :param fields_id_dict: (dictionary) Dictionary containing the ids of the
        different textboxes as keys and the value to be input as its associated values.
        :param id_next_btn: (str) Id of the formulary submission button.
        """
        self.has_form = True
        self.ids_form_dict = fields_id_dict
        self.id_form_next_btn = id_next_btn
