import os
import time
import zipfile
import requests
import pandas as pd
import csv
import chromedriver_autoinstaller

from typing import Union
from tqdm import tqdm
from bs4 import BeautifulSoup, SoupStrainer, element
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from functools import partial
from concurrent.futures import ThreadPoolExecutor

#CHROME_DRIVER_VERSION = "122.0.6261.111"
#SYSTEM = "win64"

WEB_URL = "https://www.iso-group.com/NSNIndex"

INPUT_CSV_FILENAME  = '1-search_nsn.csv'
OUTPUT_CSV_FILENAME = '3-result_nsn.csv'

FAILED_NSN_CSV_FILENAME = '3-refetch_nsn-error.csv'

MAX_THREAD_NUM = 50
MAX_HTTP_RETRIES = 10

new_output_filename = None # To avoid the function 'write_to_csv' append to different file after saving.

def read_csv(relative_path: str, refetch: bool = False) -> Union[pd.DataFrame, list]:
    if not refetch:
        df = None
        
        try:
            df = pd.read_csv(relative_path)
        except FileNotFoundError:
            print(f"Not found {relative_path}")
        except Exception as e:
            print(f"Error occurred while reading {relative_path}: {e}")
            
        return df
    else:
        refetch_nsn_list = []
        try:
            df = pd.read_csv(relative_path, header=None).squeeze("columns")
            refetch_nsn_list = df.tolist()
        except FileNotFoundError:
            return None
        except Exception as e:
            print(f"Error occurred while reading {relative_path}: {e}")
    
        return refetch_nsn_list

def write_to_csv(data: list[dict], filename: str, append: bool = False):
    global new_output_filename
    
    if not append:
        base, ext = os.path.splitext(filename)
        
        index = 1
        while os.path.exists(filename):
            index += 1
            filename = f"{base}({index}){ext}"
            new_output_filename = filename
            
            
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False, header=True)
        
        print(f"Save to {filename}")
    else:
        if new_output_filename is not None:
            filename = new_output_filename
            
        df = pd.DataFrame(data)
        df.to_csv(filename, mode='a', index=False, header=False)
    
        print(f"Append to {filename}")

def write_failed_nsn_to_csv(nsn: str, filename: str):
    df = pd.DataFrame({'NSN': [nsn]})
    
    df.to_csv(filename, mode='a', index=False, header=False)

def download_chromedriver():    
    try:
        #url = f"https://storage.googleapis.com/chrome-for-testing-public/{version}/{system}/chromedriver-{system}.zip"
        version=chromedriver_autoinstaller.get_chrome_version()
        if version is None:
            chromedriver_autoinstaller.install()  # Check if the current version of chromedriver exists
        else:
            print(f"Chromedriver {version} already exists. Skipping download.")
        #webdriver.Chrome().get(url="http://www.python.org")
    except Exception as e:
        print(f"Error occurred while downloading web driver: {e}")

def mount_driver(url: str) -> webdriver.Chrome:
    try:
        options = Options()
        options.add_argument('--headless') 
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument("--incognito")
        options.add_argument("--disable-plugins-discovery")
        options.add_argument("--no-sandbox")
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-notifications')

        #service = Service(executable_path=f"chromedriver-{SYSTEM}/chromedriver.exe")
        service = webdriver.ChromeService()
        driver = webdriver.Chrome(service=service, options=options)

        driver.get(url)
        
        time.sleep(1)
        
        return driver
    except Exception as e:
        print(f"Error occurred while mounting web driver: {e}")

def fetch_nsn(page_source: str) -> set: 
    result_set = set()
    
    try:
        soup = BeautifulSoup(page_source, 'lxml', parse_only=SoupStrainer('div', 'message-body'))  

        table = soup.find('table', class_="table table-hover")
        
        if table is None:
            return result_set

        a_elems = table.find_all('a')
        
        if a_elems and a_elems[0].text.strip() == "None Found":
            return result_set
        else:
            for a in a_elems:
                result_set.add(a.text)
    except Exception as e:
        print(f'Error occurred when fetching nsn: {e}')
    
    return result_set

def set_item_info(item_name: str, dd_tags: element.ResultSet) -> tuple:
    """pack item_info into tuple.

    Args:
        nsn (str): nsn of item
        item_name (str): name of item
        dd_tags (element.ResultSet): bs4.element.ResultSet from find_all('dd')

    Returns:
        tuple: contains (item_name, federal_supply_classification, national_item_identification_number,
                        codification_country, item_name_code, criticality, hazardous_material_indicator_code)
    """
    
    federal_supply_classification = ''
    national_item_identification_number = ''
    codification_country = ''
    item_name_code = ''
    criticality = ''
    hazardous_material_indicator_code = ''

    dd_tags_num = len(dd_tags)
    
    # Federal Supply Classification
    # National Item Identification Number
    # Codification Country
    # Item Name Code
    # Criticality
    # Hazardous Material Indicator Code
    
    try:
        if dd_tags_num == 3:
            federal_supply_classification = dd_tags[0].text.strip()
            national_item_identification_number = dd_tags[1].text.strip()
            codification_country = dd_tags[2].text.strip()
        elif dd_tags_num == 5:
            federal_supply_classification = dd_tags[0].text.strip()
            national_item_identification_number = dd_tags[1].text.strip()
            codification_country = dd_tags[2].text.strip()
            criticality = dd_tags[3].text.strip()
            hazardous_material_indicator_code = dd_tags[4].text.strip()
        elif dd_tags_num == 6:
            federal_supply_classification = dd_tags[0].text.strip()
            national_item_identification_number = dd_tags[1].text.strip()
            codification_country = dd_tags[2].text.strip()
            item_name_code = dd_tags[3].text.strip()
            criticality = dd_tags[4].text.strip()
            hazardous_material_indicator_code = dd_tags[5].text.strip()
        else:
            raise Exception
    except Exception as e:
        print(f'Error when set item info: {e}')
        
    return (item_name, federal_supply_classification, national_item_identification_number, \
            codification_country, item_name_code, criticality, hazardous_material_indicator_code)

def fetch_nsn_info(session: requests.Session, pbar: tqdm, keyy:str, nsn: str) -> dict:
    result_dict = dict()
    item_info_tuple = tuple()
    pn_set = set()
    
    url = f'https://www.iso-group.com/NSN/{nsn}'
    
    try:
        result_dict['key'] = keyy
        result_dict['NSN'] = nsn
        if (nsn==" "):
            result_dict['Item Name'] = ""
            result_dict['Federal Supply Classification'] = ""
            result_dict['National Item Identification Number'] = ""
            result_dict['Codification Country'] = ""
            result_dict['Item Name Code'] = ""
            result_dict['Criticality'] = ""
            result_dict['Hazardous Material Indicator Code'] = ""
            result_dict['Part Number List'] = ""
            pbar.update(1)
            return result_dict
        else:
            response = session.get(url, timeout=(5, 30))
            
    except requests.exceptions.ReadTimeout:
        write_failed_nsn_to_csv(nsn, FAILED_NSN_CSV_FILENAME)
        return {}
    except Exception as e:
        print(f'Error occurred when getting session: {e}')
        write_failed_nsn_to_csv(nsn, FAILED_NSN_CSV_FILENAME)
        return {}
        
    try:
        # item info
        section_soup = BeautifulSoup(response.text, 'lxml', parse_only=SoupStrainer('section', id='NSNDetailPage'))
        div_element = section_soup.find('div', class_='list-group-item')
        if div_element is None:
            return result_dict   
        first_small_elems = div_element.find('small', {'class': 'text-primary'})
        second_small_elems = first_small_elems.find_next('small', {'class': 'text-primary'})
        item_name = second_small_elems.text.strip()
        
        dl_tag = div_element.find('dl', {'class': 'dl-horizontal2b text-primary'})
        if dl_tag is None:
            return result_dict     
        dd_tags = dl_tag.find_all('dd')
        item_info_tuple = set_item_info(item_name, dd_tags)
        
        result_dict['Item Name'] = item_info_tuple[0]
        result_dict['Federal Supply Classification'] = item_info_tuple[1]
        result_dict['National Item Identification Number'] = item_info_tuple[2]
        result_dict['Codification Country'] = item_info_tuple[3]
        result_dict['Item Name Code'] = item_info_tuple[4]
        result_dict['Criticality'] = item_info_tuple[5]
        result_dict['Hazardous Material Indicator Code'] = item_info_tuple[6]
    except Exception as e:
        print(f'Error occurred when fetching item info: {e}')
        write_failed_nsn_to_csv(nsn, FAILED_NSN_CSV_FILENAME)
        return {}
        
    try:
        # pn
        pn_soup = BeautifulSoup(response.text, 'lxml', parse_only=SoupStrainer('div', class_='column associatedPartsColumn'))
        
        a_elems = pn_soup.find_all('a')
        
        for a in a_elems:
            pn = a.text
            if len(pn) == 1: # RNCC or RNVC
                continue
            pn_set.add(pn)
        
        result_dict['Part Number List'] = list(pn_set)
    except Exception as e:
        print(f'Error occurred when fetching pn list: {e}')
        write_failed_nsn_to_csv(nsn, FAILED_NSN_CSV_FILENAME)
        return {}
    
    pbar.update(1)
    return result_dict

def search(driver: webdriver.Chrome, query: str) -> set:
    nsn_set = set()
    
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "ctl00_Search1_tbSearch")))
        
        search_box = driver.find_element(By.ID, "ctl00_Search1_tbSearch")
        search_box.clear()
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        cur_url = driver.current_url

        if 'NSN' in cur_url:
            nsn = cur_url.split('/')[-1]
            nsn_set.add(nsn)
        else:
            fetching_nsn = True
            while fetching_nsn:
                nsn_set.update(fetch_nsn(driver.page_source))
                next_page_btn = WebDriverWait(driver, 10, 0.3, ignored_exceptions=(NoSuchElementException, StaleElementReferenceException)) \
                    .until(EC.presence_of_element_located((By.NAME, "ctl00$cphMain$SearchNSN1$dpNSNSearch$ctl02$ctl00")))
                
                if next_page_btn.is_enabled():
                    next_page_btn.click()
                else:
                    fetching_nsn = False
    except Exception as e:
        print(f"Error occurred while searching: {e}")
        
    return nsn_set
    
if __name__ == "__main__":
    
    df = pd.read_csv(INPUT_CSV_FILENAME, header=None)
    
    if df is not None:
        download_chromedriver()
        driver = mount_driver(WEB_URL)
        
        # fetch nsn
        nsn_set = dict()
        with tqdm(total=len(df.columns), desc='Fetching NSN') as pbar:
            for col in df.loc[0]:
                print(str(col))
                s1=search(driver, str(col))
                if (not s1):
                    s1=set()
                nsn_set.update({str(col):s1})
                pbar.update(1)
        driver.quit()
        
        # fetch nsn info and write into csv
        data = list()
        session = requests.Session()
        http_adapter = requests.adapters.HTTPAdapter(max_retries=MAX_HTTP_RETRIES)
        session.mount('http:/', http_adapter)
        
        with tqdm(total=len(nsn_set), desc='Fetching NSN Info') as pbar:
            for keyy1 in nsn_set.keys():
                detail1 = nsn_set[keyy1]
                partial_fetch = partial(fetch_nsn_info, session, pbar, keyy1)
                #data = list(map(partial_fetch, (nsn for nsn in detail1)))
                with ThreadPoolExecutor(max_workers=MAX_THREAD_NUM) as executor:
                    data.extend(list(executor.map(partial_fetch, (nsn for nsn in detail1))))
        session.close()
        
        #data = [x for x in data if x] # To remove empty dict
        keys = data[0].keys()
        with open(OUTPUT_CSV_FILENAME, 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(data)
        #write_to_csv(data, OUTPUT_CSV_FILENAME) # the same
    
    # refetch nsn info
    refetch_list = read_csv(FAILED_NSN_CSV_FILENAME, refetch=True)
    if refetch_list is not None:
        os.remove(FAILED_NSN_CSV_FILENAME)
    
        refetch_tried = 1
        max_refetch_tried = 3
        while (refetch_list is not None) and \
                (len(refetch_list) > 0) and \
                (refetch_tried <= max_refetch_tried):        
            data = []
            session = requests.Session()
            http_adapter = requests.adapters.HTTPAdapter(max_retries=3)
            session.mount('http:/', http_adapter)
        
            with tqdm(total=len(refetch_list), desc=f'{refetch_tried}. Re-fetching NSN Info') as pbar:
                partial_fetch = partial(fetch_nsn_info, session, pbar)
                with ThreadPoolExecutor(max_workers=MAX_THREAD_NUM) as executor:
                    data = list(executor.map(partial_fetch, (nsn for nsn in refetch_list)))
                
            session.close()
        
            data = [x for x in data if x] # To remove empty dict
        
            write_to_csv(data, OUTPUT_CSV_FILENAME, append=True)
        
            refetch_tried += 1
        
            refetch_list = read_csv(FAILED_NSN_CSV_FILENAME, refetch=True)
            if refetch_list is not None:
                os.remove(FAILED_NSN_CSV_FILENAME)
        
