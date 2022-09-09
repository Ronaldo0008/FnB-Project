from codecs import ignore_errors
from distutils.log import error
from selenium_module import webdriver
from bs4 import BeautifulSoup as BS
import pandas as pd
import numpy as np
import time
import json
import requests

import warnings
warnings.filterwarnings("ignore")


def selenium_scrap(pub_url):                                                                                            # This function uses Selenium
    driver = webdriver.Firefox(executable_path=r'C:\Users\fredr\Downloads\geckodriver-v0.31.0-win64\geckodriver.exe')   # Need to download geckodriver from google
    driver.get(pub_url)

    while True:
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")                                # this line of code will allow us to scroll down to the bottom of the page
            time.sleep(30) 
            script_label = driver.find_elements("xpath","//script[@type = 'application/ld+json']")                  # Locating application/ld+json element in the page
            data_address = script_label[2].get_attribute('innerText')                                               # Get the second application/ld+json element in the page
            data=script_label[3].get_attribute('innerText')
            break
        except:
            pass

    # Name of the Pubs & image URL
    zomato_data_json = json.loads(data)
    zomato_data= pd.DataFrame.from_records(zomato_data_json['item'],columns=['type', 'name', 'image'])
    zomato_data['type']= zomato_data['type'].replace(np.nan,'Pubs')                                                 # Assigns the rest type
    zomato_data.insert(0, 'position', range(1, 1 + len(zomato_data)))                       
    print(zomato_data.head())

    # Address of the Pubs
    zomato_data_address_json = json.loads(data_address)
    zomato_data_adress= pd.DataFrame.from_records(zomato_data_address_json['itemListElement'],columns=['type', 'position', 'url'])
    zomato_data_adress['type']= zomato_data_adress['type'].replace(np.nan,'Pubs')
    print(zomato_data_adress.head())

    zomato = pd.merge(zomato_data, zomato_data_adress[['position','url']], on=['position'])
    zomato['id']=zomato['image'].str.replace('/chains','').str.split('/').str[6]
    return zomato

# Get the number of pages
def number_of_pages(url):                                                                                       # This function uses Beautiful soup
    url =url +str(1)
    agent = requests.get(url,headers={"User-Agent":"Mozilla/5.0",'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'})
    tag =BS(agent.content, 'html.parser')
    pages = json.loads(tag.text)['page_data']['sections']['SECTION_REVIEWS']['numberOfPages']
    return pages

# Scrapping Reviews
def reviews(url, pages):                                                                                        # This function uses Beautiful soup
    print(pages)
    # Creating New Dataframe
    review=pd.DataFrame()
    
    for page in range(1,pages):
        try:
            urls = url + str(page)
            print(urls)
            agent = requests.get(urls,headers={"User-Agent":"Mozilla/5.0",'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
        'Accept-Encoding': 'none',
        'Accept-Language': 'en-US,en;q=0.8',
        'Connection': 'keep-alive'})
            time.sleep(5)
            tag =BS(agent.content, 'html.parser')
            reviews = json.loads(tag.text)['entities']['REVIEWS']
            reviews = pd.DataFrame(reviews).T  
            print(page,pages)
            if (reviews['timestamp'].str.contains('2019')).any() == True:
                review_filter = reviews[~reviews['timestamp'].str.contains("2019")]                     # Applying filter to remove 2019 records
                review= review.append(review_filter)
                return review
            elif pages == page+1:                                                                       # Usually the last page have 0 comments - so iterating till last second page
                review= review.append(reviews)  
                return review
            else :
                review= review.append(reviews) 
        except:
            pass 


if __name__=='__main__':
    pub_url="https://www.zomato.com/bangalore/koramangala-restaurants/bar"
    zomato = selenium_scrap(pub_url)                                                                                           # In this function we pull the rest details like name , ID, etc.

    counter = 0
    # Looping through the restraunt ids
    for ids in list(zomato['id']):      
        try:                                                                                                                   # Used try block to tackle timeout issue
            url = "https://www.zomato.com/webroutes/reviews/loadMore?sort=dd&filter=reviews-dd&res_id="+ str(ids)+"&page="     # sort == dd in the url means the data is sorted from latest to oldest
            pages = number_of_pages(url)                                                                                       # Get the number of review page for each rest
            zomato_review = reviews(url, pages)
            zomato_review['rest_id']=ids                                                                                       # assign ID for each rest after fetching the data
            zomato_review.to_excel('reviews_'+str(ids)+'.xlsx')
        except KeyError as e:
            pass
            

    