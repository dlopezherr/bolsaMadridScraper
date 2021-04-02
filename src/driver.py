
from selenium import webdriver



def chrome_driver(driver_path):
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_argument('--disable-extensions')
    driver = webdriver.Chrome(driver_path, chrome_options=options)
    return driver
