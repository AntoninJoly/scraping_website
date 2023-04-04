from selenium import webdriver
import selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--headless=new")
options.add_experimental_option('excludeSwitches', ['enable-logging'])
# options.add_argument('--window-size=1920,1200')

from tqdm import tqdm
import numpy as np
import pandas as pd
import time
# import requests
# from bs4 import BeautifulSoup, Tag
# from urllib.request import Request, urlopen
# import re
import logging
import os
import sys

from utils import *

class logPython:
    def __init__(self):
        logging.basicConfig(filename="../log/event.log",
                            filemode='a',
                            format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
                            datefmt='%H:%M:%S',
                            level = logging.DEBUG)
        self.logger = logging.getLogger()

col = ['path','title','MSRP','xchange price','dealer name','dealer place',
       'dealer phone','vin','hours','miles','color','year','Condition','Displacement',
       'Engine type','Dry weight','Fuel capacity','Instruments / Display']

log = logPython()
URL = 'https://polarisxchange.com/vehicles'
path = get_url_path(URL)
df_final = pd.DataFrame(columns=col)

for idx, url in enumerate(tqdm(path)):
    try:
        driver_pages = webdriver.Chrome(options=options)
        driver_pages.get(url)
        time.sleep(1.5)
        try:
            df_final = pd.concat([df_final, scrape_page(driver_pages, col)],axis=0)
        except Exception as e:
            log.logger.error(f'Cannot scrape data from webpage, msg={e}\n########')
        driver_pages.quit()
    except Exception as e:
        log.logger.error(f'Cannot access webpage, msg={e}\n########')

    df_final.to_csv('../data/scraping_file.csv',index=False)