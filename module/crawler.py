import urllib.request
import json
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time

### Naver API에서 뉴스 항목을 불러옵니다.

def get_news_list(crawling_trg, client_id, client_secret):
    news_list = []
    for step in range(1, 1100, 100):
        if step == 1001:
            step = 1000
        
        params = dict(
            query=urllib.parse.quote(crawling_trg),
            display=urllib.parse.quote('100'), 
            start=urllib.parse.quote(str(step)),
            sort=urllib.parse.quote('date'),
        )

        url = f"https://openapi.naver.com/v1/search/news?query={params['query']}&display={params['display']}&start={params['start']}&sort={params['sort']}"

        request = urllib.request.Request(url)
        request.add_header('X-Naver-Client-Id', client_id)
        request.add_header('X-Naver-Client-Secret', client_secret)
        response = urllib.request.urlopen(request)
        rescode = response.getcode()

        if(rescode==200):
            response_body = response.read()
            result = json.loads(response_body.decode('utf-8'))['items']
            news_list.extend(result)
        else:
            print('Error Code:' + rescode)
        
        time.sleep(1)
        
        # if step == 101:
        #     break
    
    news_list_df = pd.DataFrame(news_list).drop_duplicates()
    news_list_df['checker'] = news_list_df.link.str.find('https://n.news.naver.com/')
    news_list_df = news_list_df[news_list_df['checker'] > -1]
    news_list_df.reset_index(inplace=True)
    news_list_df['crawling_trg'] = crawling_trg
    
    return news_list_df

### Naver API에서 불러온 뉴스 항목의 본문을 불러옵니다.

def crawl_news(news_list_df, headers):
    crawled_news = []
    for idx, row in news_list_df.iterrows():
        # row.crawling_trg, row.pubDate, row.title, cleansed_news_content, row.originallink, row.link, row.description
        URL = str(row.link)
        r = requests.get(URL, headers=headers)
        
        try:
            soup = BeautifulSoup(r.content, 'html5lib')
            news_content = soup.select('#newsct_article')[0].text
            cleansed_news_content = re.sub(r'[\n\t^/$]', '', news_content)
            crawled_news.append([row.crawling_trg, row.pubDate, row.title, cleansed_news_content, row.originallink, row.link, row.description])
        except Exception as e:
            soup = BeautifulSoup(r.content, 'html5lib')
            news_content = soup.select('#articeBody')[0].text
            cleansed_news_content = re.sub(r'[\n\t^/$]', '', news_content)
            crawled_news.append([row.crawling_trg, row.pubDate, row.title, cleansed_news_content, row.originallink, row.link, row.description])
        
        time.sleep(1)
        
        # if idx == 3:
        #     break
    
    crawled_news_df = pd.DataFrame(crawled_news, columns=['crawling_trg', 'pubDate', 'title', 'content', 'originallink', 'link', 'description'])
    
    return crawled_news_df