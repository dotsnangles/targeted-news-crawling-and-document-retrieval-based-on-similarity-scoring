import urllib.request
import json
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

client_id = 'hwEnzlSdGXZTyeubesmy'
client_secret = 'WkpCvqbw6u'

def crawl_news(query):
    news_list = []
    for step in range(1, 1100, 100):
        if step == 1001:
            step = 1000

        params = dict(
            query=urllib.parse.quote('책상'),
            display=urllib.parse.quote('100'),
            start=urllib.parse.quote(str(step)),
            sort=urllib.parse.quote('date'),
        )

        url = f"https://openapi.naver.com/v1/search/news?query={params['query']}&display={params['display']}&start={params['start']}&sort={params['sort']}"

        request = urllib.request.Request(url)
        request.add_header('X-Naver-Client-Id',client_id)
        request.add_header('X-Naver-Client-Secret',client_secret)
        response = urllib.request.urlopen(request)
        rescode = response.getcode()

        if(rescode==200):
            response_body = response.read()
            result = json.loads(response_body.decode('utf-8'))['items']
            news_list.extend(result)
        else:
            print('Error Code:' + rescode)
        # print(step)
        
    news_df = pd.DataFrame(news_list).drop_duplicates()
    news_df['checker'] = news_df.link.str.find('https://n.news.naver.com/')
    news_df = news_df[news_df['checker'] > -1]
    news_df.reset_index(inplace=True)
            
    return news_df