import urllib.request
import json
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

### 네이버 developers에서 할당받은 id와 key입니다. 서빙시에는 환경 변수로 넣어두는 것이 좋을 것 같습니다.

client_id = 'hwEnzlSdGXZTyeubesmy'
client_secret = 'WkpCvqbw6u'

### https://developers.naver.com/docs/serviceapi/search/news/news.md#뉴스-검색-결과-조회
### 위 페이지를 참조하여 만든 뉴스 검색 결과를 조회해 가지고 오는 크롤러입니다.
### JSON 포맷으로 'pubDate', 'title', 'originallink', 'link', 'description' 다섯가지 항목을 불러옵니다.
### 쿼리 요청시에 파라미터로 정렬이 가능합니다. 관련도와 날짜 최신순으로 가능하며 현재 날짜 최신순으로 설정되어 있습니다.
### 불러올 수 있는 항목의 최대 수는 1100개입니다.
### 아래의 함수로 불러온 리스트를 바탕으로 main.py에서 본문 크롤링이 진행됩니다.

def crawl_news_list(query):
    news_list = []
    
    # 항목을 100개씩 불러오며 마지막 인덱스를 네이버 API에서 허용하는 최대값인 1000으로 바꿔줍니다.
    # 인덱스의 최소값은 1로 허용되어 있습니다.
    for step in range(1, 1100, 100):
        if step == 1001:
            step = 1000
        
        # 네이버 API의 파라미터를 설정하기 위한 코드입니다.
        params = dict(
            query=urllib.parse.quote(query),
            display=urllib.parse.quote('100'), # 항목을 100개씩 불러오기 위한 설정입니다. 최대 허용 수치는 100입니다.
            start=urllib.parse.quote(str(step)),
            sort=urllib.parse.quote('date'),
        )

        # 설정한 파라미터를 리퀘스트를 수행할 url에 넣습니다.
        url = f"https://openapi.naver.com/v1/search/news?query={params['query']}&display={params['display']}&start={params['start']}&sort={params['sort']}"

        # 네이버 developers에서 할당받은 id와 key를 넣습니다.
        request = urllib.request.Request(url)
        request.add_header('X-Naver-Client-Id',client_id)
        request.add_header('X-Naver-Client-Secret',client_secret)
        response = urllib.request.urlopen(request)
        rescode = response.getcode()

        # 응답 코드가 200이 나오면 결과를 가지고 옵니다. 그렇지 않은 경우 에러 메세지를 표시합니다.
        # 최상단에 선언한 news_list에 하나씩 붙여넣기를 수행합니다.
        if(rescode==200):
            response_body = response.read()
            result = json.loads(response_body.decode('utf-8'))['items']
            news_list.extend(result)
        else:
            print('Error Code:' + rescode)
        # print(step)
    
    # 편리한 후처리를 위해 판다스의 데이터 프레임으로 변환합니다.
    # 중복되는 행을 제거해줍니다.
    # 또한 네이버 뉴스에 등록되지 않은 뉴스는 제외합니다.
    news_df = pd.DataFrame(news_list).drop_duplicates()
    news_df['checker'] = news_df.link.str.find('https://n.news.naver.com/')
    news_df = news_df[news_df['checker'] > -1]
    news_df.reset_index(inplace=True)
    
    # 데이터 프레임 변환 작업이 끝나면 반환해줍니다.
    return news_df