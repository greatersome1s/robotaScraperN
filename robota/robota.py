from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import robota.constant as const
from time import sleep
from math import floor
import csv
from pathlib import Path

class Robota(webdriver.Chrome):
    def __init__(self, options = None, service = None, keep_alive = True):
        super().__init__(options, service, keep_alive)
        self.info = []
        self.implicitly_wait(4)
        
    def start_page(self):
        self.get(const.BASE_URL1)
        
    def choose_location(self, location="Вся Україна"):
        self.find_element(By.TAG_NAME, "alliance-jobseeker-city-dropdown").click()
        try:
            input = WebDriverWait(self, 5).until(EC.visibility_of_element_located((By.XPATH, '//label[text()=" Почніть вводити місто "]/preceding-sibling::input')))
            input.clear()
            input.send_keys(location)
        except:
            print('element not found')
        self.find_element(By.XPATH, f"//span[@class='santa-text-red-500' and text()='{location}']").click()
        
    # Requires to send job type from constants on calling
    def choose_worktype(self, job_string=const.FULL_TIME): 
        self.find_element(By.XPATH, f"//p[text()='{const.WORKBUTTON_NAME}']/..").click()
        self.find_element(By.XPATH, f"//p[text()='{job_string}']/..").click()
        
    # Requires to send salary type from constants on calling
    def choose_salary(self, salary_string = const.SALARY_ANY, hide_without_salary=False):
        self.find_element(By.TAG_NAME, "lib-vacancies-salary-desktop-list-filter").click()
        self.find_element(By.XPATH, f"//div[text()='{salary_string}']").click()
        if hide_without_salary:
            self.find_element(By.TAG_NAME, "lib-vacancies-salary-desktop-list-filter").click()
            self.find_element(By.XPATH, "//input[contains(@id, 'toggler-')]/following-sibling::span").click()
            
    # Requires to send list with constants to filter on calling
    def filter(self, filter_list: list = [const.FILTER_REMOTE]):
        newlist = filter_list
        self.implicitly_wait(2)
        if const.FILTER_REMOTE in filter_list:
            newlist.remove(const.FILTER_REMOTE)
            self.find_element(By.XPATH, f"//span[text()='{const.FILTER_REMOTE}']/preceding-sibling::span").click()
        elif const.FILTER_UNEXPERIENCED in filter_list:
            newlist.remove(const.FILTER_UNEXPERIENCED)
            self.find_element(By.XPATH, f"//span[text()='{const.FILTER_UNEXPERIENCED}']/preceding-sibling::span").click()
        if len(newlist)!=0:
            self.find_element(By.XPATH, f"//santa-button[@type='additional']").click()
            self.implicitly_wait(2)
            for i in newlist:
                if i==const.FILTER_WORKLOCATION_OFFICE or i==const.FILTER_WORKLOCATION_HYBRID:
                    self.find_element(By.XPATH, f"//p[text()='{i}']/..").click()
                else:
                    self.find_element(By.XPATH, f"//span[text()='{i}']").click()
            self.find_element(By.XPATH, "//button[text()=' Застосувати ']").click()
        
    # Requires to send job name to search
    def search_job(self, job_name):
        self.search_text = job_name
        input = self.find_element(By.XPATH, "//santa-suggest-input/descendant::input")
        input.clear()
        input.send_keys(job_name)
        listing_section = self.find_element(By.TAG_NAME, "alliance-jobseeker-desktop-vacancies-list")
        self.find_element(By.XPATH, "//alliance-jobseeker-search/descendant::button").click()
        try:
            # primary: wait until the previous listing becomes stale (page updated)
            WebDriverWait(self, 2).until(EC.staleness_of(listing_section))
            print('stale')
        except Exception:
            # fallback: wait until the listing text changes or a new listing element is present
            try:
                # finds if the listing section text is not text of previous listing section
                WebDriverWait(self, 2).until(lambda d: d.find_element(By.TAG_NAME, "alliance-jobseeker-desktop-vacancies-list").text != listing_section.text)
                print("!=text")
            except Exception:
                pass
                #WebDriverWait(self, 5).until(EC.presence_of_element_located((By.TAG_NAME, "alliance-jobseeker-desktop-vacancies-list")))
        
        
    def parse(self):
        listing_section_locator = (By.TAG_NAME, "alliance-jobseeker-desktop-vacancies-list")
        zapros_url = self.current_url
        if self.find_element(By.TAG_NAME, "santa-pagination-with-links").text!="":
            try:
                pages = int(self.find_element(By.TAG_NAME, "santa-pagination-with-links").find_element(By.XPATH, ".//a[last()]").text)
            except:
                pages = int(self.find_element(By.TAG_NAME, "santa-pagination-with-links").find_element(By.XPATH, ".//a[last()-1]").text)
        else:
            pages = 1
            
        current_page = 1
            
        def parse_first_page():
            listing_section = self.find_element(*listing_section_locator)
            # scroll to pagination and then to middle
            middle = floor(len(listing_section.find_elements(By.TAG_NAME, "alliance-vacancy-card-desktop"))/2)
            pagination = self.find_element(By.TAG_NAME, "santa-pagination-with-links")
            self.execute_script('arguments[0].scrollIntoView(false);', pagination.find_element(By.XPATH, f".//parent::div/preceding-sibling::div"))
            for i in self.find_element(*listing_section_locator).find_elements(By.TAG_NAME, "div"):
                self.execute_script("arguments[0].scrollIntoView(false);", i)
            #self.execute_script("arguments[0].scrollIntoView(false);", pagination.find_element(By.XPATH, f".//parent::div/preceding-sibling::div[{middle}]"))
            # get all elements after loading
            listing_section = self.find_element(*listing_section_locator)
            job_listings = listing_section.find_elements(By.TAG_NAME, "alliance-vacancy-card-desktop")
            for i in job_listings:
                # will use to find other info later on so don't convert to text
                job_name = i.find_element(By.TAG_NAME, 'h2')
                try:
                    job_salary = job_name.find_element(
                        By.XPATH,
                        ".//following-sibling::div/span"
                    ).text.strip()
                    if "₴" in job_salary:
                        pass
                    else:
                        job_salary = "Не вказано"
                except:
                    job_salary = "Не вказано"
                # find mutual parent for company info and location
                mparent = job_name.find_element(By.XPATH, ".//following-sibling::div[2]")
                job_company = mparent.find_element(By.TAG_NAME, 'span').text
                job_location = mparent.find_element(By.XPATH, ".//span[2]").text
                self.info.append({
                    "Title": job_name.text,
                    'Salary': job_salary,
                    'Company': job_company,
                    'Location': job_location
                })
                
            return listing_section
                
        def next_page(listing_section):
            nonlocal current_page
            current_page+=1
            next_url = ""
            if 'params;' in zapros_url:
                url_list = zapros_url.split(";")
                url_list.insert(1, f"page={current_page}")
                for i in url_list:
                    next_url+=i
                    next_url+=";"
                next_url.rstrip(";")
            else:
                next_url = zapros_url + f"/params;page={current_page}"
            print(next_url)
            self.get(next_url)
            WebDriverWait(self, 5).until(EC.staleness_of(listing_section))
            new_listing_section = WebDriverWait(self, 5).until(EC.presence_of_element_located(listing_section_locator))
            WebDriverWait(self, 5).until(EC.presence_of_element_located((By.TAG_NAME, "alliance-vacancy-card-desktop")))
            return new_listing_section
            
        def parse(listing_section):
            # scroll to pagination and then to middle
            middle = floor(len(listing_section.find_elements(By.TAG_NAME, "alliance-vacancy-card-desktop"))/2)
            pagination = self.find_element(By.TAG_NAME, "santa-pagination-with-links")
            self.execute_script('arguments[0].scrollIntoView(false);', pagination.find_element(By.XPATH, f".//parent::div/preceding-sibling::div"))
            for i in self.find_element(*listing_section_locator).find_elements(By.TAG_NAME, "div"):
                self.execute_script("arguments[0].scrollIntoView(false);", i)
            #self.execute_script("arguments[0].scrollIntoView(false);", pagination.find_element(By.XPATH, f".//parent::div/preceding-sibling::div[{middle}]"))
            # get all elements after loading
            listing_section = self.find_element(*listing_section_locator)
            job_listings = listing_section.find_elements(By.TAG_NAME, "alliance-vacancy-card-desktop")
            for i in job_listings:
                # will use to find other info later on so don't convert to text
                job_name = i.find_element(By.TAG_NAME, 'h2')
                try:
                    job_salary = job_name.find_element(
                        By.XPATH,
                        ".//following-sibling::div/span"
                    ).text.strip()
                    if "₴" in job_salary:
                        pass
                    else:
                        job_salary = "Не вказано"
                except:
                    job_salary = "Не вказано"
                # find mutual parent for company info and location
                mparent = job_name.find_element(By.XPATH, ".//following-sibling::div[2]")
                job_company = mparent.find_element(By.TAG_NAME, 'span').text
                job_location = mparent.find_element(By.XPATH, ".//span[2]").text
                self.info.append({
                    "Title": job_name.text,
                    'Salary': job_salary,
                    'Company': job_company,
                    'Location': job_location
                })
        
        if pages==1:
            parse_first_page()
        else:
            listing_section = parse_first_page()
            for i in range(pages-1):
                new_listing_section = next_page(listing_section)
                parse(new_listing_section)
                
    def save(self, file_name=None):
        # generate file name if not given
        if file_name==None:
            file_name=self.search_text.strip().replace(" ", "-") + ".csv"
        
        fieldnames_ = [
            'Title', 'Salary', 'Company', 'Location'
        ]
        
        file_path = Path(__file__).parent.parent/"csvStorage"/file_name
        
        if file_path.is_file():
            toadd_list = []
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                row_list = []
                for row in reader:
                    row_list.append(row)
                print(row_list)
        else:
            with open(file_path, "w", encoding="utf-8", newline="") as f:
                dictWriter = csv.DictWriter(f, fieldnames=fieldnames_)
                dictWriter.writeheader()
                for row in self.info:
                    dictWriter.writerow(row)