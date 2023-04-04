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
import requests
from bs4 import BeautifulSoup, Tag
from urllib.request import Request, urlopen
import re

import logging
import os
import sys

def get_url_path(URL):
    driver = webdriver.Chrome(options=options)
    driver.get(URL)
    time.sleep(5)
    num_pages = [i.text for i in driver.find_elements(By.CLASS_NAME, 'pagination__link')]
    num_pages = np.max([int(i) for i in num_pages if i.isnumeric()])
    path = [URL] + ['https://polarisxchange.com/vehicles?page=%s'%(i) for i in np.arange(2, num_pages+1)]
    driver.quit()
    return path

def scrape_page(driver, col, list_rows = []):
    df_res = pd.DataFrame(columns=col)
    name = 'card__image-container'
    for items in driver.find_elements(By.CLASS_NAME, name):
        path = items.get_attribute('href')
        if path!=None:
            try:
                df_res = pd.concat([df_res, scrape_data(path, col)],axis=0)
            except Exception as e:
                log.logger.error(f'func=scrape_page, msg={e}\n########')
    return df_res

def scrape_class(soup, tag, res):
    for t in soup.find_all(class_=tag):
        try:
            r = [i for i in t.text.split('\n') if i !='' and i.strip()]
            if len(r) == 1:
                res[r[0]] = None
            elif len(r) == 2:
                res[r[0]] = r[1]
        except Exception as e:
            log.logger.error(f'func=scrape_class, msg={e}\n########')
    return res

def scrape_data(path, col):
    page = requests.get(path)
    soup = BeautifulSoup(page.content, 'html.parser')
    
    res = {}
    res['path'] = path
    try:
        p = soup.find('h1', {'class': 'vdp-title'}).get_text().split('\n')
        p = [i.strip() for i in p if i.strip()!=''][0]
        res['title'] = p
    except:
        res['title'] = 'Could not retrieve'

    # Xchange price
    try:
        # p = soup.find('p', {'class': 'waterfall__price'}).get_text().split('\n')
        # p = [i.strip() for i in p if i.strip()!=''][0]

        p = [i.text.split('\n') for i in soup.find_all('div', {'class':'waterfall__item'})]
        p = [[j for j in i if j.strip() and j!=''] for i in p]
        p = [i for i in p if ('Polaris Xchange Price' in i)]
        p = [i for i in p if len(i) in [2,3]]
        p = set(tuple(i) for i in p)
        p = [[i for i in j if any(s.isdigit() for s in i) or (i.lower().replace(' ','')=='notavailable')] for j in p]
        p = [i for s in p for i in s][0]

        res['xchange price'] = p
    except:
        res['xchange price'] = 'Could not retrieve'

    # MSRP
    try:
        p = [i.text.split('\n') for i in soup.find_all('div', {'class':'waterfall__item'})]
        p = [[j for j in i if j.strip() and j!=''] for i in p]
        p = [i for i in p if ('MSRP' in i) or ('Manufacturer suggested retail price' in i)]
        p = [i for i in p if len(i) in [2,3]]
        p = set(tuple(i) for i in p)
        p = [[i for i in j if any(s.isdigit() for s in i) or (i.lower().replace(' ','')=='notavailable')] for j in p]
        p = [i for s in p for i in s][0]
        res['msrp'] = p
    except:
        res['msrp'] = 'Could not retrieve'

    # Dealer name
    try:
        p = soup.find('div', {'data-role': 'vdp-dealer-info'}).get_text().split('\n')
        p = [i.strip() for i in p if i.strip()!='']
    except:
        res['dealer name'] = 'Could not retrieve'
        res['dealer place'] = 'Could not retrieve'
    try:
        res['dealer name'] = p[0]
    except:
        res['dealer name'] = 'Could not retrieve'

    # Dealer place
    try:
        res['dealer place'] = p[1]
    except:
        res['dealer place'] = 'Could not retrieve'

    # Phone number
    try:
        p = [i.split('\n') for i in soup.find('p', {'class': 'media__body'})]
        p = [i for s in p for i in s]
        p = [i.strip() for i in p if i.strip()!=''][0]
        res['dealer phone'] = p
    except:
        res['dealer phone'] = 'Could not retrieve'

    # VIN, Stocks, Hours, Miles, Hours, Year, Condition
    res = scrape_class(soup, 'vehicle-specs__content', res)
    
    # Dry Weight, Fuel Capacity, Height, Length, Person Capacity, Width, Bore and Stroke, Displacement, 
    # Engine Type, Final Drive, Starting System, Front Brake, Front Suspension, Rear Brake, Rear Suspension, 
    # Track Type, Color, Instruments/Display
    res = scrape_class(soup, 'description-list__item', res)
    res = {k.lower():v for k, v in res.items()}

    data = [res['path'], # link
            res['title'], # title
            res['xchange price'], # xchange price
            res['msrp'], # msrp
            res['dealer name'], # Dealer name
            res['dealer place'], # Dealer place
            res['dealer phone'], # Dealer phone
            res.get('vin'), # VIN
            res.get('hours'), # Hours
            res.get('miles'), # Miles
            res.get('color'), # Color
            res.get('year'), # Year
            res.get('condition'), # Condition
            res.get('displacement'), # Displacement
            res.get('engine type'), # Engine type
            res.get('dry weight'), # Dry weight
            res.get('fuel capacity'), # Fuel capacity
            res.get('instument/displays') # Instrument / Display
            ]
    df = pd.DataFrame.from_dict({k:[v] for k,v in zip(col, data)})
    return df