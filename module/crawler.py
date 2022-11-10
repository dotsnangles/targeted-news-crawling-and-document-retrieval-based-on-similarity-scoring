import urllib.request
import json
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
from datetime import datetime


### Naver API에서 뉴스 항목을 불러옵니다.
def get_news_list(target, keyword, client_id, client_secret):
    crawling_trg = ' '.join([target, keyword])
    
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
    # print(news_list_df.columns)
    
    try:
        news_list_df['checker'] = news_list_df.link.str.find('https://n.news.naver.com/')
        news_list_df = news_list_df[news_list_df['checker'] > -1]
        news_list_df.reset_index(inplace=True)
        news_list_df['crawling_trg'] = crawling_trg
        news_list_df['keyword'] = keyword
        news_list_df['target'] = target
        return news_list_df
    except Exception as e:
        print(e)
        time_stamp = str(datetime.now())
        news_list_df.to_csv(f'crawling_errors/{crawling_trg}_{e}_{time_stamp}.csv', index=False, encoding='utf-8-sig')
        return None


### Naver API에서 불러온 뉴스 항목의 본문을 불러옵니다.
def crawl_news(target, keyword, news_list_df, headers):
    crawled_news = []
    for idx, row in news_list_df.iterrows():
        # row.target, row.keyword, row.pubDate, row.title, cleansed_news_content, row.originallink, row.link, row.description
        URL = str(row.link)
        r = requests.get(URL, headers=headers)
        
        try:
            soup = BeautifulSoup(r.content, 'html5lib')
            news_content = soup.select('#newsct_article')[0].text
            cleansed_news_content = re.sub(r'[\n\t^/$]', '', news_content)
            crawled_news.append([row.target, row.keyword, row.pubDate, row.title, cleansed_news_content, row.originallink, row.link, row.description])
        except Exception as e:
            try:
                soup = BeautifulSoup(r.content, 'html5lib')
                news_content = soup.select('#articeBody')[0].text
                cleansed_news_content = re.sub(r'[\n\t^/$]', '', news_content)
                crawled_news.append([row.target, row.keyword, row.pubDate, row.title, cleansed_news_content, row.originallink, row.link, row.description])
            except Exception as e:
                print(e)
                print('다음 주소의 문서를 크롤링하지 못 했습니다.')
                print(f'{str(row.link)}')
        
        time.sleep(1)
        
        # if idx == 1:
        #     break
    
    crawled_news_df = pd.DataFrame(crawled_news, columns=['target', 'keyword', 'pubDate', 'title', 'content', 'originallink', 'link', 'description'])
    
    ### 쿼리와 기관명이 들어가 있는 기사만 추려냅니다.
    search_target = crawled_news_df.content.str.contains(target, case=False, regex=True)
    search_keyword = crawled_news_df.content.str.contains(keyword, case=False, regex=True)
    crawled_news_df = crawled_news_df[search_target & search_keyword].copy().reset_index(drop=True)
    
    return crawled_news_df