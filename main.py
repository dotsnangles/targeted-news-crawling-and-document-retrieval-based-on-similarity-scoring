import time
import re
import argparse
import requests
import pandas as pd
from bs4 import BeautifulSoup
from module.crawler import crawl_news

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", dest="query", action="store")
    args = parser.parse_args()

    news_df = crawl_news(args.query)

    articles = []

    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
        'cookie': 'nid_inf=1417715440; NID_AUT=jB6JKkl0bQJkzabA2sqcsZPcc58lN3Nk/oKjGyVYl1n8PedB7ujlxHdECKcm9kS7; NID_JKL=CdIfrElqYRkes7uT/S10prytLgVd7C1HBLS0nz55Sys=; VISIT_LOG_CLEAN=1; NFS=2; NID_SES=AAABkxQsSdlab5VkBVUMJHd12mikXaT/HRo/rtzzaxgjXmXJLfOFG25S5TiaZsFNk5bLeRF4Ej3UoZTevQC7Jd7fVFOAFJtSFoNgapi8qqUTVHDqzpWo4zUjmx/LD5cdsWbvaL/cByCai8XYLRLdB0o6W7sQutPmRMFUblZMKU/CdpBh8aziLA/i9wHRgkCr4zpYxc/YROLyZLZ7QmphI5qakKYHN4OxNKYy/Dp+PvlCsWk6azoXw7AxABwR/NdLMwDxNgZ6yN0iUJDkWFFPEN0yBGCm5VaOa1oF4tU0GkLMQsbyMb/+mOw6aBjxQNSgS5RDsn3Vs6H9l1qczNtasU4OpdonIK0EzoLYyQEgLkpXeLTnzkdaJnqR7EyjKjl8hH/EsaVdnRaAEs0afY3VK8f+pCn0z/5n9xpiCd0UVrpoI3nwF1No4x/mEk71EW2ghH90hyg/9F0KHAHLneYZ6lCvcdhE/ENHrmc1nP0R0sUnOltV0XIyf0fEua7rvSqv0P0iuE0xD2+WUqh//96WFUP+XyeQxvn16XPBT8PSfE/nU/FQ; nx_ssl=2; page_uid=h1WRNsp0YiRssKvZbrNssssssMh-389234; BMR='
    }

    # 네이버뉴스 일반: #newsct_article 연예: #articeBody
    for idx, row in news_df.iterrows():
        # row.title, row.originallink, row.link, row.description, row.pubDate,
        URL = str(row.link)
        r = requests.get(URL, headers=headers)
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
        
        # time.sleep(5)
        
        if idx == 10:
            break

    result = pd.DataFrame(articles, columns=['pubDate', 'title', 'body', 'originallink', 'link', 'description'])
    result.to_csv(f'{args.query}_crawled.csv', index=False)

if __name__ == '__main__':
    main()