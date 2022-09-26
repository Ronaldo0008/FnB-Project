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

def order_item(zomato_review):
    final=pd.DataFrame()

    for i in list(zomato_review['url']):
        i = i.replace('info','')
        print('https://www.zomato.com/webroutes/getPage?page_url='+i+'order')
        agent = requests.get('https://www.zomato.com/webroutes/getPage?page_url='+i+'order',headers={"User-Agent":"Mozilla/5.0",'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                'Accept-Encoding': 'none',
                'Accept-Language': 'en-US,en;q=0.8',
                'Connection': 'keep-alive'})
        # time.sleep(5)
        tag =BS(agent.content, 'html.parser')

        for j in range(0,50):
            for k in [0,2]:
                for l in range(0,30):
                    try:
                        reviews_xx = json.loads(tag.text)['page_data']['order']['menuList']['menus'][j]['menu']['categories'][k]['category']['items'][l]['item']
                        main_menu_xx=json.loads(tag.text)['page_data']['order']['menuList']['menus'][j]['menu']['categories'][k]['category']['items'][l]['item']['search_alias']
                        rest_id = json.loads(tag.text)['page_info']['resId']
                        reviews_xx= pd.DataFrame.from_dict(reviews_xx, orient='index')
                        reviews_xx = reviews_xx.transpose()
                        reviews_xx['Dish_type']=main_menu_xx
                        reviews_xx['rest_id']=rest_id
                        final=final.append(reviews_xx)
                    except:
                        pass

    return final

def overview(zomato_review):   
    final_df=pd.DataFrame()
    final=pd.DataFrame()
    for i in list(zomato_review['url']):
        i = i.replace('info','')
        agent = requests.get('https://www.zomato.com/webroutes/getPage?page_url='+i,headers={"User-Agent":"Mozilla/5.0",'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
            'Accept-Encoding': 'none',
            'Accept-Language': 'en-US,en;q=0.8',
            'Connection': 'keep-alive'})
        time.sleep(5)
        tag =BS(agent.content, 'html.parser')

        # Fetching Data
        rest_id = json.loads(tag.text)['page_info']['resId']
        is_perm_closed = json.loads(tag.text)['page_data']['sections']['SECTION_BASIC_INFO']['is_perm_closed']
        is_temp_closed = json.loads(tag.text)['page_data']['sections']['SECTION_BASIC_INFO']['is_temp_closed']
        is_opening_soon = json.loads(tag.text)['page_data']['sections']['SECTION_BASIC_INFO']['is_opening_soon']
        should_ban_ugc = json.loads(tag.text)['page_data']['sections']['SECTION_BASIC_INFO']['should_ban_ugc']
        is_shelled = json.loads(tag.text)['page_data']['sections']['SECTION_BASIC_INFO']['is_shelled']
        media_alert = json.loads(tag.text)['page_data']['sections']['SECTION_BASIC_INFO']['media_alert']
        is_delivery_only = json.loads(tag.text)['page_data']['sections']['SECTION_BASIC_INFO']['is_delivery_only']
        # title = json.loads(tag.text)['page_data']['sections']['SECTION_RES_DETAILS']['PEOPLE_LIKED']['title']
        # description = json.loads(tag.text)['page_data']['sections']['SECTION_RES_DETAILS']['PEOPLE_LIKED']['description']
        cuisine = json.loads(tag.text)['page_data']['sections']['SECTION_BASIC_INFO']['cuisine_string']
        timing = json.loads(tag.text)['page_data']['sections']['SECTION_BASIC_INFO']['timing']['timing_desc']
        locality  = json.loads(tag.text)['page_data']['sections']['SECTION_RES_HEADER_DETAILS']['LOCALITY']['text']

        final_df.loc[0,'is_perm_closed'] = is_perm_closed
        final_df['rest_id'] = rest_id
        final_df['is_temp_closed']= is_temp_closed
        final_df['is_opening_soon']= is_opening_soon
        final_df['should_ban_ugc']= should_ban_ugc
        final_df['is_shelled']= is_shelled
        final_df['media_alert']= media_alert
        final_df['is_delivery_only']= is_delivery_only
        # final_df['title']= title
        # final_df['description']= description
        final_df['cuisine']= cuisine
        final_df['timing']= timing
        final_df['locality']= locality
        highlights = pd.DataFrame(json.loads(tag.text)['page_data']['sections']['SECTION_RES_DETAILS']['HIGHLIGHTS']['highlights'])[['text','type']].T
        new_header = highlights.iloc[0]
        highlights.columns = new_header
        highlights = highlights[1:].reset_index()
        details =pd.DataFrame.from_dict(json.loads(tag.text)['page_data']['sections']['SECTION_RES_CONTACT'], orient='index').T
        df = pd.concat([final_df, highlights,details], axis=1)
        final=final.append(df)
    return final


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

    # Pull order list data
    order_list = order_item(zomato_review)
    # Pull overview data
    overview_of_the_rest = overview(zomato_review)
            

   
