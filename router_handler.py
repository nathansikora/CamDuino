from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from time import sleep
from threading import Thread
from json import load

with open('settings.json', 'r') as ff:
    dd = load(ff)['router_handler']
    DRIVER_PATH = dd['DRIVER_PATH']
    BRAVE_PATH = dd['BRAVE_PATH']
    ROUTER_ADDRESS = dd['ROUTER_ADDRESS']
    PASS = dd['PASS']

DRIVER_PATH = r"C:\Users\Nathan\Downloads\chromedriver_win32\chromedriver.exe"
BRAVE_PATH = r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe"
ROUTER_ADDRESS = 'http://192.168.1.1'
PASS = 'gor47tim'
SLEEP_TIME_SEC = 30


class RouterHandler:
    def __init__(self, router_addr=ROUTER_ADDRESS, driver_path=DRIVER_PATH, brave_path=BRAVE_PATH):
        self.clients = {}
        self.router_addr = router_addr

        option = webdriver.ChromeOptions()
        option.binary_location = brave_path
        option.add_argument("--incognito")
        option.add_argument("--headless")

        self.browser = webdriver.Chrome(executable_path=driver_path, chrome_options=option)
        clnt_thr = Thread(target=self.get_clients)
        clnt_thr.start()

    def is_client(self, clients):
        if hasattr(clients, '__iter__'):
            return any(client in self.clients for client in clients)
        else:
            return clients in self.clients

    def wait_until_id(self, id, wait_time=10):
        try:
            WebDriverWait(self.browser, wait_time).until(expected_conditions.presence_of_element_located((By.ID, id)))
        except:
            return False
        return True

    def get_clients(self):
        while True:
            try:
                browser = self.browser
                browser.delete_all_cookies()
                browser.get(self.router_addr)
                self.wait_until_id("pc-login-password")
                pass_inp = browser.find_element_by_id("pc-login-password")
                pass_inp.clear()
                pass_inp.send_keys(PASS)
                self.wait_until_id("pc-login-btn")
                browser.find_element_by_id("pc-login-btn").click()
                if self.wait_until_id("confirm-yes", 5):
                    browser.find_element_by_id("confirm-yes").click()
            except:
               browser.quit()
               self.__init__()

            while True:
                try:
                    self.wait_until_id("map_icon_wireless")
                    get_clients_butt = browser.find_element_by_id("map_icon_wireless")
                    get_clients_butt.click()
                    sleep(5)
                    self.clients = self.get_clients_from_tbl()
                finally:
                    sleep(SLEEP_TIME_SEC)

    def get_clients_from_tbl(self):
        vals = []
        clients = {}
        browser = self.browser
        tbl = browser.find_element_by_id("tableWlStat")
        elements = tbl.find_elements_by_class_name('table-content')
        for j, elem in enumerate(elements):
            try:
                if not elem.is_displayed():
                    browser.find_element_by_class_name('right').click()

                val = elem.text if elem.text != '' else elem.find_element_by_class_name('tp-input-text').get_attribute(
                    'value')
                vals.append(val)
            except: pass
        for k in range(0, len(vals), 4):
            clients[vals[k + 2]] = vals[k + 1]
        return clients