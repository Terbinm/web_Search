import os
import time
import requests
import csv
import io
import tempfile
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import List, Dict, Any, Union, Set
from bs4 import BeautifulSoup, SoupStrainer
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
import chromedriver_autoinstaller

from flask import current_app
from app import db
from app.models.nsn import NSN


class NsnService:
    """NSN查詢服務"""

    WEB_URL = "https://www.iso-group.com/NSNIndex"
    MAX_THREAD_NUM = 10  # 限制線程數量，避免過多請求
    MAX_HTTP_RETRIES = 5

    def __init__(self, app=None):
        """初始化NSN服務，傳入Flask應用實例"""
        self.app = app
        self.logger = logging.getLogger(__name__)

        # 檢查/安裝chromedriver
        try:
            version = chromedriver_autoinstaller.get_chrome_version()
            if version is None:
                chromedriver_autoinstaller.install()
        except Exception as e:
            self.logger.error(f"Error while checking/installing chromedriver: {str(e)}")

    def mount_driver(self) -> webdriver.Chrome:
        """初始化WebDriver"""
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

            service = webdriver.ChromeService()
            driver = webdriver.Chrome(service=service, options=options)

            driver.get(self.WEB_URL)
            time.sleep(1)

            return driver
        except Exception as e:
            self.logger.error(f"Error mounting web driver: {str(e)}")
            raise Exception(f"無法初始化WebDriver: {str(e)}")

    def search(self, driver: webdriver.Chrome, query: str) -> Set[str]:
        """使用WebDriver搜尋NSN"""
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
                    nsn_set.update(self.fetch_nsn(driver.page_source))
                    next_page_btn = WebDriverWait(driver, 10, 0.3, ignored_exceptions=(
                    NoSuchElementException, StaleElementReferenceException)) \
                        .until(
                        EC.presence_of_element_located((By.NAME, "ctl00$cphMain$SearchNSN1$dpNSNSearch$ctl02$ctl00")))

                    if next_page_btn.is_enabled():
                        next_page_btn.click()
                        # 等待頁面加載
                        time.sleep(1)
                    else:
                        fetching_nsn = False

        except Exception as e:
            self.logger.error(f"Error searching NSN: {str(e)}")

        return nsn_set

    def fetch_nsn(self, page_source: str) -> Set[str]:
        """從頁面源碼中提取NSN"""
        result_set = set()

        try:
            soup = BeautifulSoup(page_source, 'html.parser', parse_only=SoupStrainer('div', 'message-body'))

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
            self.logger.error(f"Error fetching NSN: {str(e)}")

        return result_set

    def set_item_info(self, item_name: str, dd_tags: List[Any]) -> tuple:
        """處理物品信息"""
        federal_supply_classification = ''
        national_item_identification_number = ''
        codification_country = ''
        item_name_code = ''
        criticality = ''
        hazardous_material_indicator_code = ''

        dd_tags_num = len(dd_tags)

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
        except Exception as e:
            self.logger.error(f"Error setting item info: {str(e)}")

        return (item_name, federal_supply_classification, national_item_identification_number,
                codification_country, item_name_code, criticality, hazardous_material_indicator_code)

    def fetch_nsn_info(self, session: requests.Session, key: str, nsn: str) -> Dict[str, Any]:
        """獲取NSN詳細信息"""
        result_dict = {}
        item_info_tuple = tuple()
        pn_set = set()

        url = f'https://www.iso-group.com/NSN/{nsn}'

        try:
            result_dict['key'] = key
            result_dict['NSN'] = nsn

            if nsn == " ":
                # 處理空白NSN
                result_dict['Item_Name'] = ""
                result_dict['Federal_Supply_Classification'] = ""
                result_dict['National_Item_Identification_Number'] = ""
                result_dict['Codification_Country'] = ""
                result_dict['Item_Name_Code'] = ""
                result_dict['Criticality'] = ""
                result_dict['Hazardous_Material_Indicator_Code'] = ""
                result_dict['Part_Number_List'] = []
                return result_dict

            # 查詢數據庫中是否已存在 (在調用此方法前應確保在應用上下文中)
            if self.app and self.app.app_context:
                with self.app.app_context():
                    nsn_obj = NSN.query.filter_by(nsn=nsn).first()
                    if nsn_obj:
                        # 使用數據庫中的數據
                        result_dict['Item_Name'] = nsn_obj.item_name
                        result_dict['Federal_Supply_Classification'] = nsn_obj.federal_supply_classification
                        result_dict['National_Item_Identification_Number'] = nsn_obj.national_item_identification_number
                        result_dict['Codification_Country'] = nsn_obj.codification_country
                        result_dict['Item_Name_Code'] = nsn_obj.item_name_code
                        result_dict['Criticality'] = nsn_obj.criticality
                        result_dict['Hazardous_Material_Indicator_Code'] = nsn_obj.hazardous_material_indicator_code
                        result_dict['Part_Number_List'] = nsn_obj.part_numbers
                        return result_dict

            # 從網絡獲取數據
            response = session.get(url, timeout=(5, 30))

        except requests.exceptions.ReadTimeout:
            result_dict['error'] = 'Request timed out'
            return result_dict
        except Exception as e:
            self.logger.error(f"Error getting session: {str(e)}")
            result_dict['error'] = str(e)
            return result_dict

        try:
            # 解析物品信息
            section_soup = BeautifulSoup(response.text, 'html.parser',
                                         parse_only=SoupStrainer('section', id='NSNDetailPage'))
            div_element = section_soup.find('div', class_='list-group-item')

            if div_element is None:
                return result_dict

            first_small_elems = div_element.find('small', {'class': 'text-primary'})
            if first_small_elems is None:
                return result_dict

            second_small_elems = first_small_elems.find_next('small', {'class': 'text-primary'})
            if second_small_elems is None:
                return result_dict

            item_name = second_small_elems.text.strip()

            dl_tag = div_element.find('dl', {'class': 'dl-horizontal2b text-primary'})
            if dl_tag is None:
                return result_dict

            dd_tags = dl_tag.find_all('dd')
            item_info_tuple = self.set_item_info(item_name, dd_tags)

            result_dict['Item_Name'] = item_info_tuple[0]
            result_dict['Federal_Supply_Classification'] = item_info_tuple[1]
            result_dict['National_Item_Identification_Number'] = item_info_tuple[2]
            result_dict['Codification_Country'] = item_info_tuple[3]
            result_dict['Item_Name_Code'] = item_info_tuple[4]
            result_dict['Criticality'] = item_info_tuple[5]
            result_dict['Hazardous_Material_Indicator_Code'] = item_info_tuple[6]
        except Exception as e:
            self.logger.error(f"Error fetching item info: {str(e)}")
            result_dict['error'] = f'解析物品信息出錯: {str(e)}'
            return result_dict

        try:
            # 解析料號信息
            pn_soup = BeautifulSoup(response.text, 'html.parser',
                                    parse_only=SoupStrainer('div', class_='column associatedPartsColumn'))

            a_elems = pn_soup.find_all('a')

            for a in a_elems:
                pn = a.text
                if len(pn) == 1:  # RNCC or RNVC
                    continue
                pn_set.add(pn)

            result_dict['Part_Number_List'] = list(pn_set)

            # 存儲到數據庫 (在應用上下文中)
            if self.app and self.app.app_context:
                with self.app.app_context():
                    try:
                        nsn_obj = NSN(
                            nsn=nsn,
                            item_name=result_dict['Item_Name'],
                            federal_supply_classification=result_dict['Federal_Supply_Classification'],
                            national_item_identification_number=result_dict['National_Item_Identification_Number'],
                            codification_country=result_dict['Codification_Country'],
                            item_name_code=result_dict['Item_Name_Code'],
                            criticality=result_dict['Criticality'],
                            hazardous_material_indicator_code=result_dict['Hazardous_Material_Indicator_Code'],
                            part_number_list=','.join(result_dict['Part_Number_List']) if result_dict[
                                'Part_Number_List'] else None,
                            source_key=key
                        )
                        db.session.add(nsn_obj)
                        db.session.commit()
                    except Exception as e:
                        db.session.rollback()
                        self.logger.error(f"Error saving NSN to database: {str(e)}")

        except Exception as e:
            self.logger.error(f"Error fetching part numbers: {str(e)}")
            result_dict['Part_Number_List'] = []
            result_dict['error'] = f'解析料號信息出錯: {str(e)}'

        return result_dict

    def search_single_nsn(self, query: str) -> List[Dict[str, Any]]:
        """單一NSN查詢"""
        results = []

        try:
            # 確保在應用上下文中運行數據庫查詢
            if self.app:
                with self.app.app_context():
                    # 首先檢查資料庫是否已有該NSN的資料
                    nsn_obj = NSN.query.filter_by(nsn=query).first()
                    if nsn_obj:
                        results.append({
                            'NSN': nsn_obj.nsn,
                            'Item_Name': nsn_obj.item_name,
                            'Federal_Supply_Classification': nsn_obj.federal_supply_classification,
                            'National_Item_Identification_Number': nsn_obj.national_item_identification_number,
                            'Codification_Country': nsn_obj.codification_country,
                            'Item_Name_Code': nsn_obj.item_name_code,
                            'Criticality': nsn_obj.criticality,
                            'Hazardous_Material_Indicator_Code': nsn_obj.hazardous_material_indicator_code,
                            'Part_Number_List': nsn_obj.part_numbers,
                            'key': nsn_obj.source_key
                        })
                        return results

                    # 或者查詢以query作為source_key的NSN
                    nsn_objs = NSN.query.filter_by(source_key=query).all()
                    if nsn_objs:
                        for nsn_obj in nsn_objs:
                            results.append({
                                'NSN': nsn_obj.nsn,
                                'Item_Name': nsn_obj.item_name,
                                'Federal_Supply_Classification': nsn_obj.federal_supply_classification,
                                'National_Item_Identification_Number': nsn_obj.national_item_identification_number,
                                'Codification_Country': nsn_obj.codification_country,
                                'Item_Name_Code': nsn_obj.item_name_code,
                                'Criticality': nsn_obj.criticality,
                                'Hazardous_Material_Indicator_Code': nsn_obj.hazardous_material_indicator_code,
                                'Part_Number_List': nsn_obj.part_numbers,
                                'key': nsn_obj.source_key
                            })
                        return results

            # 如果資料庫中沒有，則使用WebDriver查詢
            driver = self.mount_driver()
            nsn_set = self.search(driver, query)
            driver.quit()

            if not nsn_set:
                return []

            # 使用線程池獲取NSN詳情
            session = requests.Session()
            http_adapter = requests.adapters.HTTPAdapter(max_retries=self.MAX_HTTP_RETRIES)
            session.mount('http://', http_adapter)
            session.mount('https://', http_adapter)

            # 使用partial函數預設部分參數
            partial_fetch = partial(self.fetch_nsn_info, session, query)

            with ThreadPoolExecutor(max_workers=self.MAX_THREAD_NUM) as executor:
                # 使用線程池並行獲取NSN詳情
                results = list(executor.map(partial_fetch, (nsn for nsn in nsn_set)))

            session.close()

            # 過濾掉可能的空結果
            results = [result for result in results if result]

        except Exception as e:
            self.logger.error(f"Error in single NSN search: {str(e)}")
            raise Exception(f"單一NSN查詢出錯: {str(e)}")

        return results

    def search_batch_nsn(self, nsn_list: List[str]) -> List[Dict[str, Any]]:
        """批量NSN查詢"""
        results = []

        try:
            # 確保在應用上下文中運行數據庫查詢
            db_results = []
            if self.app:
                with self.app.app_context():
                    for nsn in nsn_list:
                        nsn_obj = NSN.query.filter_by(nsn=nsn).first()
                        if nsn_obj:
                            db_results.append({
                                'NSN': nsn_obj.nsn,
                                'Item_Name': nsn_obj.item_name,
                                'Federal_Supply_Classification': nsn_obj.federal_supply_classification,
                                'National_Item_Identification_Number': nsn_obj.national_item_identification_number,
                                'Codification_Country': nsn_obj.codification_country,
                                'Item_Name_Code': nsn_obj.item_name_code,
                                'Criticality': nsn_obj.criticality,
                                'Hazardous_Material_Indicator_Code': nsn_obj.hazardous_material_indicator_code,
                                'Part_Number_List': nsn_obj.part_numbers,
                                'key': nsn_obj.source_key
                            })
                        else:
                            # 還要查詢以nsn作為source_key的NSN
                            nsn_objs = NSN.query.filter_by(source_key=nsn).all()
                            for obj in nsn_objs:
                                db_results.append({
                                    'NSN': obj.nsn,
                                    'Item_Name': obj.item_name,
                                    'Federal_Supply_Classification': obj.federal_supply_classification,
                                    'National_Item_Identification_Number': obj.national_item_identification_number,
                                    'Codification_Country': obj.codification_country,
                                    'Item_Name_Code': obj.item_name_code,
                                    'Criticality': obj.criticality,
                                    'Hazardous_Material_Indicator_Code': obj.hazardous_material_indicator_code,
                                    'Part_Number_List': obj.part_numbers,
                                    'key': obj.source_key
                                })

            # 過濾掉已在數據庫中的NSN
            db_nsns = set([result['NSN'] for result in db_results])
            remaining_nsns = [nsn for nsn in nsn_list if nsn not in db_nsns]

            # 如果數據庫中已有所有NSN，直接返回
            if not remaining_nsns:
                return db_results

            # 獲取剩餘NSN的詳情
            driver = self.mount_driver()

            all_nsn_set = {}
            for nsn in remaining_nsns:
                try:
                    nsn_set = self.search(driver, nsn)
                    all_nsn_set[nsn] = nsn_set
                except Exception as e:
                    self.logger.error(f"Error searching NSN {nsn}: {str(e)}")

            driver.quit()

            # 使用線程池獲取NSN詳情
            session = requests.Session()
            http_adapter = requests.adapters.HTTPAdapter(max_retries=self.MAX_HTTP_RETRIES)
            session.mount('http://', http_adapter)
            session.mount('https://', http_adapter)

            web_results = []
            for key, nsn_set in all_nsn_set.items():
                partial_fetch = partial(self.fetch_nsn_info, session, key)

                with ThreadPoolExecutor(max_workers=self.MAX_THREAD_NUM) as executor:
                    batch_results = list(executor.map(partial_fetch, (nsn for nsn in nsn_set)))

                web_results.extend([result for result in batch_results if result])

            session.close()

            # 合併數據庫結果和網絡結果
            results = db_results + web_results

        except Exception as e:
            self.logger.error(f"Error in batch NSN search: {str(e)}")
            raise Exception(f"批量NSN查詢出錯: {str(e)}")

        return results

    def get_nsn_details(self, nsn: str) -> Dict[str, Any]:
        """獲取NSN詳情"""
        try:
            # 確保在應用上下文中運行數據庫查詢
            if self.app:
                with self.app.app_context():
                    # 首先檢查資料庫
                    nsn_obj = NSN.query.filter_by(nsn=nsn).first()
                    if nsn_obj:
                        return {
                            'NSN': nsn_obj.nsn,
                            'Item_Name': nsn_obj.item_name,
                            'Federal_Supply_Classification': nsn_obj.federal_supply_classification,
                            'National_Item_Identification_Number': nsn_obj.national_item_identification_number,
                            'Codification_Country': nsn_obj.codification_country,
                            'Item_Name_Code': nsn_obj.item_name_code,
                            'Criticality': nsn_obj.criticality,
                            'Hazardous_Material_Indicator_Code': nsn_obj.hazardous_material_indicator_code,
                            'Part_Number_List': nsn_obj.part_numbers,
                            'key': nsn_obj.source_key
                        }

            # 如果數據庫中沒有，直接使用session獲取
            session = requests.Session()
            http_adapter = requests.adapters.HTTPAdapter(max_retries=self.MAX_HTTP_RETRIES)
            session.mount('http://', http_adapter)
            session.mount('https://', http_adapter)

            result = self.fetch_nsn_info(session, "", nsn)
            session.close()

            return result

        except Exception as e:
            self.logger.error(f"Error getting NSN details: {str(e)}")
            raise Exception(f"獲取NSN詳情出錯: {str(e)}")