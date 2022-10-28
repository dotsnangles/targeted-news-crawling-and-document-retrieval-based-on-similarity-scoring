import time
import re
import argparse
import requests
import pandas as pd
from bs4 import BeautifulSoup
from module.crawler import crawl_news_list

### 실행 방법
### python main.py --query "키워드"

def main():
    # 터미널 실행시 argument를 받기 위한 코드입니다.
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", dest="query", action="store")
    args = parser.parse_args()

    # 네이버 API에서 키워드로 검색된 뉴스의 목록을 불러옵니다.
    news_df = crawl_news_list(args.query)

    # 이제부터 크롤링할 본문을 저장해둘 리스트입니다.
    articles = []

    # 접근 권한을 획득하기 위해 브라우저의 user-agent와 cookie를 가지고 왔습니다.
    # 크롤러가 작동하지 않을 경우 cookie를 변경해주면 다시 작동합니다.
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
        'cookie': 'nid_inf=1417715440; NID_AUT=jB6JKkl0bQJkzabA2sqcsZPcc58lN3Nk/oKjGyVYl1n8PedB7ujlxHdECKcm9kS7; NID_JKL=CdIfrElqYRkes7uT/S10prytLgVd7C1HBLS0nz55Sys=; VISIT_LOG_CLEAN=1; NFS=2; NID_SES=AAABkxQsSdlab5VkBVUMJHd12mikXaT/HRo/rtzzaxgjXmXJLfOFG25S5TiaZsFNk5bLeRF4Ej3UoZTevQC7Jd7fVFOAFJtSFoNgapi8qqUTVHDqzpWo4zUjmx/LD5cdsWbvaL/cByCai8XYLRLdB0o6W7sQutPmRMFUblZMKU/CdpBh8aziLA/i9wHRgkCr4zpYxc/YROLyZLZ7QmphI5qakKYHN4OxNKYy/Dp+PvlCsWk6azoXw7AxABwR/NdLMwDxNgZ6yN0iUJDkWFFPEN0yBGCm5VaOa1oF4tU0GkLMQsbyMb/+mOw6aBjxQNSgS5RDsn3Vs6H9l1qczNtasU4OpdonIK0EzoLYyQEgLkpXeLTnzkdaJnqR7EyjKjl8hH/EsaVdnRaAEs0afY3VK8f+pCn0z/5n9xpiCd0UVrpoI3nwF1No4x/mEk71EW2ghH90hyg/9F0KHAHLneYZ6lCvcdhE/ENHrmc1nP0R0sUnOltV0XIyf0fEua7rvSqv0P0iuE0xD2+WUqh//96WFUP+XyeQxvn16XPBT8PSfE/nU/FQ; nx_ssl=2; page_uid=h1WRNsp0YiRssKvZbrNssssssMh-389234; BMR='
    }

    # 본문 크롤링을 시작합니다. 네이버 뉴스 연예의 경우 html tag의 class와 id가 다른 카테고리와는 다릅니다.
    # 따라서 예외처리를 해줍니다.
    # 네이버뉴스 일반: #newsct_article 연예: #articeBody
    # 뉴스 항목의 리스트(news_df)를 반복문에 넣어줍니다.
    for idx, row in news_df.iterrows():
        # row.title, row.originallink, row.link, row.description, row.pubDate,
        URL = str(row.link)
        r = requests.get(URL, headers=headers)
        
        # 연예 카테고리의 태그를 잡지 못 해 생기는 에러를 회피하기 위한 코드가 except로 추가되어 있습니다.
        try:
            soup = BeautifulSoup(r.content, 'html5lib')
            article = soup.select('#newsct_article')[0].text
            cleansed_article = re.sub(r'[\n\t^/$]', '', article)
            articles.append([row.pubDate, row.title, cleansed_article, row.originallink, row.link, row.description,])
        except Exception as e:
            soup = BeautifulSoup(r.content, 'html5lib')
            article = soup.select('#articeBody')[0].text
            cleansed_article = re.sub(r'[\n\t^/$]', '', article)
            articles.append([row.pubDate, row.title, cleansed_article, row.originallink, row.link, row.description,])
        
        # 반복적인 크롤링으로 인해 ban 당하는 것을 예방하기 위해 시간 지연 명령을 넣었습니다.
        time.sleep(5)
        
        # 테스트를 위해 열개만 추출한 뒤 멈추는 코드입니다.
        # if idx == 10:
        #     break

    result = pd.DataFrame(articles, columns=['pubDate', 'title', 'body', 'originallink', 'link', 'description'])
    result.to_csv(f'{args.query}_crawled.csv', index=False)

if __name__ == '__main__':
    main()